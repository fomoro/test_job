using Microsoft.EntityFrameworkCore;
using AutoMapper;
using Application.DTOs;
using Application.Interfaces;
using Infrastructure.Data;
using System.Data;
using Microsoft.Data.SqlClient;

namespace Infrastructure.Repositories
{
    public class UsuarioRepository : IUsuarioRepository
    {
        private readonly ApplicationDbContext _context;
        private readonly IMapper _mapper;

        public UsuarioRepository(ApplicationDbContext context, IMapper mapper)
        {
            _context = context;
            _mapper = mapper;
        }

        public async Task<UsuarioDto> GetUsuarioByIdAsync(int id, CancellationToken cancellationToken)
        {
            var connection = _context.Database.GetDbConnection();
            await connection.OpenAsync(cancellationToken);

            var command = connection.CreateCommand();
            command.CommandText = "sp_GetUsuarioById";
            command.CommandType = CommandType.StoredProcedure;

            var parameter = new SqlParameter("@Id", SqlDbType.Int) { Value = id };
            command.Parameters.Add(parameter);

            using (var reader = await command.ExecuteReaderAsync(cancellationToken))
            {
                if (await reader.ReadAsync(cancellationToken))
                {
                    var usuario = new UsuarioDto
                    {
                        Id = reader.GetInt32(0),
                        Nombre = reader.GetString(1),
                        Telefono = reader.GetString(2),
                        Direccion = reader.GetString(3),
                        MunicipioId = reader.GetInt32(4)
                    };

                    return usuario;
                }
                else
                {
                    return null;
                }
            }
        }

        public async Task<int> CreateUsuarioAsync(UsuarioDto usuarioDto, CancellationToken cancellationToken)
        {
            var connection = _context.Database.GetDbConnection();
            await connection.OpenAsync(cancellationToken);

            var command = connection.CreateCommand();
            command.CommandText = "sp_InsertUsuario";
            command.CommandType = CommandType.StoredProcedure;

            command.Parameters.Add(new SqlParameter("@Nombre", SqlDbType.NVarChar, 100) { Value = usuarioDto.Nombre });
            command.Parameters.Add(new SqlParameter("@Telefono", SqlDbType.NVarChar, 20) { Value = usuarioDto.Telefono });
            command.Parameters.Add(new SqlParameter("@Direccion", SqlDbType.NVarChar, 200) { Value = usuarioDto.Direccion });
            command.Parameters.Add(new SqlParameter("@MunicipioId", SqlDbType.Int) { Value = usuarioDto.MunicipioId });

            using (var reader = await command.ExecuteReaderAsync(cancellationToken))
            {
                if (await reader.ReadAsync(cancellationToken))
                {
                    return Convert.ToInt32(reader.GetDecimal(0));
                }
                return 0;
            }
        }
    }
}
