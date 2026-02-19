using Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Infrastructure.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options)
        {
        }

        public DbSet<Usuario> Usuarios { get; set; }
        public DbSet<Municipio> Municipios { get; set; }
        public DbSet<Departamento> Departamentos { get; set; }
        public DbSet<Pais> Paises { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Configuración de las relaciones
            modelBuilder.Entity<Municipio>()
                .HasMany(m => m.Usuarios)
                .WithOne(u => u.Municipio)
                .HasForeignKey(u => u.MunicipioId);

            modelBuilder.Entity<Departamento>()
                .HasMany(d => d.Municipios)
                .WithOne(m => m.Departamento)
                .HasForeignKey(m => m.DepartamentoId);

            modelBuilder.Entity<Pais>()
                .HasMany(p => p.Departamentos)
                .WithOne(d => d.Pais)
                .HasForeignKey(d => d.PaisId);
        }
    }
}
