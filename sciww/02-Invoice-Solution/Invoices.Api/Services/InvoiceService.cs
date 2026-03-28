using Invoices.Api.Models;
using System.Collections.Generic;
using System.Linq;

namespace Invoices.Api.Services;

public class InvoiceService : IInvoiceService
{
    public ValidationResponse ValidateInvoice(Invoice invoice)
    {
        if (invoice.Id <= 0)
            return new ValidationResponse { IsValid = false, ErrorMessage = "Id debe ser mayor a 0." };

        if (invoice.AccountId < 0)
            return new ValidationResponse { IsValid = false, ErrorMessage = "AccountId no puede ser negativo." };

        if (string.IsNullOrWhiteSpace(invoice.Description))
            return new ValidationResponse { IsValid = false, ErrorMessage = "Description es requerida." };

        if (invoice.Total < 0)
            return new ValidationResponse { IsValid = false, ErrorMessage = "Total no puede ser negativo." };

        if (invoice.TaxPercentage < 0 || invoice.TaxPercentage > 100)
            return new ValidationResponse { IsValid = false, ErrorMessage = "TaxPercentage debe estar entre 0 y 100." };

        return new ValidationResponse { IsValid = true, ErrorMessage = "Success" };
    }

    public float CalculateBulkSum(List<Invoice> invoices)
    {
        // Se filtran duplicados por Id usando LINQ y se suma el Total
        return invoices
            .DistinctBy(i => i.Id)
            .Sum(i => i.Total);
    }

    public TaxCalculationResult CalculateTax(Invoice invoice)
    {
        float taxAmount = invoice.Total * (invoice.TaxPercentage / 100f);
        return new TaxCalculationResult
        {
            TaxAmount = taxAmount,
            GrandTotal = invoice.Total + taxAmount
        };
    }
}