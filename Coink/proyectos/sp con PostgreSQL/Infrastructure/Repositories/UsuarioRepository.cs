using Microsoft.EntityFrameworkCore;
using AutoMapper;
using Application.DTOs;
using Application.Interfaces;
using Infrastructure.Data;
using Npgsql;
using System.Data;

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
            command.CommandText = "sp_get_usuario_by_id";
            command.CommandType = CommandType.StoredProcedure;

            var parameter = new NpgsqlParameter("p_id", NpgsqlTypes.NpgsqlDbType.Integer) { Value = id };
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
            command.CommandText = "sp_insert_usuario";
            command.CommandType = CommandType.StoredProcedure;

            command.Parameters.Add(new NpgsqlParameter("p_nombre", NpgsqlTypes.NpgsqlDbType.Varchar) { Value = usuarioDto.Nombre });
            command.Parameters.Add(new NpgsqlParameter("p_telefono", NpgsqlTypes.NpgsqlDbType.Varchar) { Value = usuarioDto.Telefono });
            command.Parameters.Add(new NpgsqlParameter("p_direccion", NpgsqlTypes.NpgsqlDbType.Varchar) { Value = usuarioDto.Direccion });
            command.Parameters.Add(new NpgsqlParameter("p_municipioid", NpgsqlTypes.NpgsqlDbType.Integer) { Value = usuarioDto.MunicipioId });

            using (var reader = await command.ExecuteReaderAsync(cancellationToken))
            {
                if (await reader.ReadAsync(cancellationToken))
                {
                    return Convert.ToInt32(reader.GetInt64(0));
                }
                return 0;
            }
        }
    }
}
