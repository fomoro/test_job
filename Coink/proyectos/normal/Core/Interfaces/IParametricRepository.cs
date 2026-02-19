using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Core.Entities;

namespace Core.Interfaces
{
    public interface IParametricRepository
    {
        Task<IEnumerable<Pais>> GetPaisesAsync();
        Task<IEnumerable<Departamento>> GetDepartamentosByPaisIdAsync(int paisId);
        Task<IEnumerable<Municipio>> GetMunicipiosByDepartamentoIdAsync(int departamentoId);
    }
}
