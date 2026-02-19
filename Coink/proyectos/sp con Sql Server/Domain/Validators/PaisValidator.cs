using Domain.Entities;
using FluentValidation;

namespace Domain.Validators
{
    public class PaisValidator : AbstractValidator<Pais>
    {
        public PaisValidator()
        {
            RuleFor(p => p.Nombre).NotEmpty().WithMessage("El nombre del país es obligatorio.");
        }
    }
}
