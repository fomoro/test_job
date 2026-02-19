using FluentValidation;

namespace Application.Usuarios.Queries
{
    public class GetUsuarioByIdQueryValidator : AbstractValidator<GetUsuarioByIdQuery>
    {
        public GetUsuarioByIdQueryValidator()
        {
            RuleFor(v => v.Id).GreaterThan(0).WithMessage("El ID del usuario debe ser mayor que 0.");
        }
    }
}
