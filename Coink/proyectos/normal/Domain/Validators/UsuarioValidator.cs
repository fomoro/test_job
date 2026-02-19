using Domain.Entities;
using FluentValidation;

namespace Domain.Validators
{
    public class UsuarioValidator : AbstractValidator<Usuario>
    {
        public UsuarioValidator()
        {
            RuleFor(u => u.Nombre).NotEmpty().WithMessage("El nombre del usuario es obligatorio.");
            RuleFor(u => u.Telefono).NotEmpty().WithMessage("El teléfono del usuario es obligatorio.");
            RuleFor(u => u.Direccion).NotEmpty().WithMessage("La dirección del usuario es obligatoria.");
            RuleFor(u => u.MunicipioId).GreaterThan(0).WithMessage("El ID del municipio debe ser mayor que 0.");
        }
    }
}



