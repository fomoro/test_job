using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Domain.Entities;
using FluentValidation;

namespace Domain.Validators
{
    public class DepartamentoValidator : AbstractValidator<Departamento>
    {
        public DepartamentoValidator()
        {
            RuleFor(d => d.Nombre).NotEmpty().WithMessage("El nombre del departamento es obligatorio.");
            RuleFor(d => d.PaisId).GreaterThan(0).WithMessage("El ID del país debe ser mayor que 0.");
        }
    }
}
