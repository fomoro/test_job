using Microsoft.EntityFrameworkCore;
using Domain.Entities;
using AutoMapper;
using Application.DTOs;
using Application.Interfaces;
using Infrastructure.Data;

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
            var usuario = await _context.Usuarios
                .Include(u => u.Municipio)
                .ThenInclude(m => m.Departamento)
                .ThenInclude(d => d.Pais)
                .FirstOrDefaultAsync(u => u.Id == id, cancellationToken);

            if (usuario == null) return null;

            return _mapper.Map<UsuarioDto>(usuario);
        }

        public async Task<int> CreateUsuarioAsync(UsuarioDto usuarioDto, CancellationToken cancellationToken)
        {
            var usuario = _mapper.Map<Usuario>(usuarioDto);

            _context.Usuarios.Add(usuario);
            await _context.SaveChangesAsync(cancellationToken);

            return usuario.Id;
        }
    }
}
