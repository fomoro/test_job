namespace Invoices.Api.Models;

public class Invoice
{
    public int Id { get; set; }
    public long AccountId { get; set; }
    public string Description { get; set; } = string.Empty;
    public float Total { get; set; }
    public int TaxPercentage { get; set; }
}