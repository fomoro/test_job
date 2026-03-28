using Microsoft.Extensions.DependencyInjection;
using FileProcessor.Console.Services;
using System.IO;


var serviceProvider = new ServiceCollection()
    .AddSingleton<NumberProcessor>()
    .BuildServiceProvider();

var processor = serviceProvider.GetRequiredService<NumberProcessor>();

string inputPath = Path.Combine("Data", "numbers.txt");
string outputPath = Path.Combine("Data", "results.txt");

Directory.CreateDirectory("Data");

processor.ProcessFile(inputPath, outputPath);