using Microsoft.AspNetCore.Mvc;
using MediatR;
using System.Threading.Tasks;
using Application.Usuarios.Commands.CreateUsuario;
using Application.Usuarios.Queries;

namespace Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UsuarioController : ControllerBase
    {
        private readonly IMediator _mediator;

        public UsuarioController(IMediator mediator)
        {
            _mediator = mediator;
        }

        [HttpPost]
        public async Task<IActionResult> CreateUsuario([FromBody] CreateUsuarioCommand command)
        {
            if (command == null)
            {
                return BadRequest("Invalid data.");
            }

            var result = await _mediator.Send(command);
            return Ok(result);
        }
        [HttpGet("{id}")] 
        public async Task<IActionResult> GetUsuarioById(int id) 
        { 
            var query = new GetUsuarioByIdQuery { Id = id }; 
            var result = await _mediator.Send(query); 
            if (result == null) 
            { 
                return NotFound(); 
            } 
            return Ok(result); 
        }

    }
}
