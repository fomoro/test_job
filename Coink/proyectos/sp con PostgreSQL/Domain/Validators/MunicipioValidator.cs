using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Domain.Entities;
using FluentValidation;

namespace Domain.Validators
{

    public class MunicipioValidator : AbstractValidator<Municipio>
    {
        public MunicipioValidator()
        {
            RuleFor(m => m.Nombre).NotEmpty().WithMessage("El nombre del municipio es obligatorio.");
            RuleFor(m => m.DepartamentoId).GreaterThan(0).WithMessage("El ID del departamento debe ser mayor que 0.");
        }
    }
}
