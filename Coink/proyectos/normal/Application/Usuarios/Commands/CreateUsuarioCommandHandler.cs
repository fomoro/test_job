using Application.DTOs;
using Application.Interfaces;
using AutoMapper;
using MediatR;
using System.Threading;
using System.Threading.Tasks;

namespace Application.Usuarios.Commands.CreateUsuario
{
    public class CreateUsuarioCommand : IRequest<int>
    {
        public string Nombre { get; set; }
        public string Telefono { get; set; }
        public string Direccion { get; set; }
        public int MunicipioId { get; set; }
    }

    public class CreateUsuarioCommandHandler : IRequestHandler<CreateUsuarioCommand, int>
    {
        private readonly IUsuarioRepository _usuarioRepository;
        private readonly IMapper _mapper;

        public CreateUsuarioCommandHandler(IUsuarioRepository usuarioRepository, IMapper mapper)
        {
            _usuarioRepository = usuarioRepository;
            _mapper = mapper;
        }

        public async Task<int> Handle(CreateUsuarioCommand request, CancellationToken cancellationToken)
        {
            var usuarioDto = _mapper.Map<UsuarioDto>(request);
            return await _usuarioRepository.CreateUsuarioAsync(usuarioDto, cancellationToken);
        }
    }
}
