using Invoices.Api.Models;
using System.Collections.Generic;

namespace Invoices.Api.Services;

public interface IInvoiceService
{
    ValidationResponse ValidateInvoice(Invoice invoice);
    float CalculateBulkSum(List<Invoice> invoices);
    TaxCalculationResult CalculateTax(Invoice invoice);
}