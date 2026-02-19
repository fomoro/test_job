using Application.DTOs;
using Application.Interfaces;
using MediatR;

namespace Application.Usuarios.Queries
{
    public class GetUsuarioByIdQuery : IRequest<UsuarioDto>
    {
        public int Id { get; set; }
    }

    public class GetUsuarioByIdQueryHandler : IRequestHandler<GetUsuarioByIdQuery, UsuarioDto>
    {
        private readonly IUsuarioRepository _usuarioRepository;

        public GetUsuarioByIdQueryHandler(IUsuarioRepository usuarioRepository)
        {
            _usuarioRepository = usuarioRepository;
        }

        public async Task<UsuarioDto> Handle(GetUsuarioByIdQuery request, CancellationToken cancellationToken)
        {
            return await _usuarioRepository.GetUsuarioByIdAsync(request.Id, cancellationToken);
        }
    }
}
