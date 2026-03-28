namespace Invoices.Api.Models;

public class ValidationResponse
{
    public bool IsValid { get; set; }
    public string? ErrorMessage { get; set; }
}