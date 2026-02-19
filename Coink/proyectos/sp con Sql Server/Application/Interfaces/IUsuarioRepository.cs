using Application.DTOs;

namespace Application.Interfaces
{
    public interface IUsuarioRepository
    {
        Task<UsuarioDto> GetUsuarioByIdAsync(int id, CancellationToken cancellationToken);
        Task<int> CreateUsuarioAsync(UsuarioDto usuarioDto, CancellationToken cancellationToken);
    }
}

