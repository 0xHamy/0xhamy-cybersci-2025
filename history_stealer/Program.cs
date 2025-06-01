// Program.cs
using System;

namespace HistoryStealer
{
    class Program
    {
        // C2 URL in plaintext
        private static readonly string C2_URL = "https://example.com";

        static void Main(string[] args)
        {
            Console.WriteLine("Program running normally.");
            // (In a real stealer, you’d use C2_URL here—
            //  but even if you never reference it at runtime,
            //  it still lives in the metadata as a literal.)
        }
    }
}
