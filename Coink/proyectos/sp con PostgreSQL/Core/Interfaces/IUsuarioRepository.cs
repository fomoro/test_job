using Core.Entities;

namespace Core.Interfaces
{
    public interface IUsuarioRepository
    {
        Task<int> InsertUsuario(Usuario usuario);
        Task<Usuario> GetUsuarioById(int id);
    }

}
