using System;
using System.IO;
using System.Linq;

namespace FileProcessor.Console.Services;

public class NumberProcessor
{
    public void ProcessFile(string inputPath, string outputPath)
    {
        if (!File.Exists(inputPath))
        {
            System.Console.WriteLine($"Error: No se encontró el archivo {inputPath}");
            return;
        }

        try
        {
            var lines = File.ReadLines(inputPath);

            var results = lines.Select(line =>
            {
                if (string.IsNullOrWhiteSpace(line)) return "Línea vacía";

                int sum = line.Where(char.IsDigit).Sum(c => (int)char.GetNumericValue(c));
                bool isMultipleOf3 = sum % 3 == 0;

                return $"{line} -> Suma: {sum} | Múltiplo de 3: {(isMultipleOf3 ? "Sí" : "No")}";
            });

            File.WriteAllLines(outputPath, results);
            System.Console.WriteLine($"Proceso terminado. Revisa el archivo: {outputPath}");
        }
        catch (Exception ex)
        {
            System.Console.WriteLine($"Ocurrió un error procesando el archivo: {ex.Message}");
        }
    }
}