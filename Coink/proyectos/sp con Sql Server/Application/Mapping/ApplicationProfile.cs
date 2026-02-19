using AutoMapper;
using Application.DTOs;
using Application.Usuarios.Commands.CreateUsuario;
using Domain.Entities;

namespace Application.Mapping
{
    public class ApplicationProfile : Profile
    {
        public ApplicationProfile()
        {
            CreateMap<CreateUsuarioCommand, UsuarioDto>();
            CreateMap<Usuario, UsuarioDto>(); 
            CreateMap<UsuarioDto, Usuario>();
        }
    }
}
