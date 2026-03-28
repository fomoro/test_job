using Invoices.Api.Models;
using Invoices.Api.Services;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace Invoices.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class InvoicesController : ControllerBase
{
    private readonly IInvoiceService _invoiceService;

    // Inyección de dependencias
    public InvoicesController(IInvoiceService invoiceService)
    {
        _invoiceService = invoiceService;
    }

    [HttpPost("validate")]
    public IActionResult Validate([FromBody] Invoice invoice)
    {
        var result = _invoiceService.ValidateInvoice(invoice);
        if (!result.IsValid) return BadRequest(result);
        return Ok(result);
    }

    [HttpPost("bulk-sum")]
    public IActionResult BulkSum([FromBody] List<Invoice> invoices)
    {
        if (invoices == null || !invoices.Any()) return BadRequest("La lista está vacía.");
        var sum = _invoiceService.CalculateBulkSum(invoices);
        return Ok(new { UniqueTotalSum = sum });
    }

    [HttpPost("tax-calculation")]
    public IActionResult CalculateTax([FromBody] Invoice invoice)
    {
        var result = _invoiceService.CalculateTax(invoice);
        return Ok(result);
    }
}