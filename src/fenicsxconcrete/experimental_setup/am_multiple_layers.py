from collections.abc import Callable

import dolfinx as df
import numpy as np
import pint
import ufl
from mpi4py import MPI
from petsc4py.PETSc import ScalarType

from fenicsxconcrete.boundary_conditions.bcs import BoundaryConditions
from fenicsxconcrete.boundary_conditions.boundary import plane_at
from fenicsxconcrete.experimental_setup.base_experiment import Experiment
from fenicsxconcrete.helper import Parameters
from fenicsxconcrete.unit_registry import ureg


class AmMultipleLayers(Experiment):
    """sets up a simple layered structure

    all layers of the same height are on top of each other, the boundary on the bottom is fixed
    the mesh includes all (activation via pseudo-density)

    """

    def __init__(self, parameters: dict[str, pint.Quantity]):
        """defines default parameters, for the rest, see base class"""

        # initialize default parameters for the setup
        default_p = Parameters()
        # default_p['dummy'] = 'example' * ureg('')  # example default parameter for this class

        # updating parameters, overriding defaults
        default_p.update(parameters)
        super().__init__(default_p)

    @staticmethod
    def default_parameters() -> dict[str, pint.Quantity]:
        '''set up a set of working values as example"""

        Returns: dictionary with required parameter

        '''
        # this must de defined in each setup class

        setup_parameters = {}
        # geometry
        setup_parameters["dim"] = 2 * ureg("")
        setup_parameters["num_layers"] = 10 * ureg("")  # number of layers in y
        setup_parameters["layer_length"] = 0.5 * ureg("m")  # x_dimension
        setup_parameters["layer_height"] = 0.01 * ureg("m")  # Dy dimension
        # only relevant for 3D case [z-dimension]
        setup_parameters["layer_width"] = 0.05 * ureg("m")

        # mesh
        setup_parameters["num_elements_layer_length"] = 10 * ureg("")
        setup_parameters["num_elements_layer_height"] = 1 * ureg("")
        # only relevant for 3D case
        setup_parameters["num_elements_layer_width"] = 2 * ureg("")

        # only relevant for 2D case
        # setup_parameters["stress_case"] = "plane_strain" # not yet implemented

        return setup_parameters

    def setup(self) -> None:
        """define the mesh for 2D and 3D"""
        self.logger.debug("setup mesh for %s", self.p["dim"])
        print(self.p["dim"])

        if self.p["dim"] == 2:
            self.mesh = df.mesh.create_rectangle(
                comm=MPI.COMM_WORLD,
                points=[(0.0, 0.0), (self.p["layer_length"], self.p["num_layer"] * self.p["layer_height"])],
                n=(self.p["num_elements_layer_length"], self.p["num_layer"] * self.p["num_elements_layer_height"]),
                cell_type=df.mesh.CellType.quadrilateral,
            )
        elif self.p["dim"] == 3:
            self.mesh = df.mesh.create_box(
                comm=MPI.COMM_WORLD,
                points=[
                    (0.0, 0.0, 0.0),
                    (self.p["layer_length"], self.p["layer_width"], self.p["num_layer"] * self.p["layer_height"]),
                ],
                n=[
                    self.p["num_elements_layer_length"],
                    self.p["num_elements_layer_width"],
                    self.p["num_layer"] * self.p["num_elements_layer_height"],
                ],
                cell_type=df.mesh.CellType.hexahedron,
            )
        else:
            raise ValueError(f'wrong dimension: {self.p["dim"]} is not implemented for problem setup')

    def create_displacement_boundary(self, V: df.fem.FunctionSpace) -> list[df.fem.bcs.DirichletBCMetaClass]:
        """define displacement boundary as fixed at bottom

        Args:
            V: function space

        Returns: list of dirichlet boundary conditions

        """
        #
        bc_generator = BoundaryConditions(self.mesh, V)

        if self.p["dim"] == 2:
            # fix dofs at bottom
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_bottom(),
                method="geometrical",
            )

        elif self.p["dim"] == 3:
            # fix dofs at bottom
            bc_generator.add_dirichlet_bc(
                np.array([0.0, 0.0, 0.0], dtype=ScalarType),
                boundary=self.boundary_bottom(),
                method="geometrical",
            )

        return bc_generator.bcs

    def create_body_force(self, v: ufl.argument.Argument) -> ufl.form.Form:
        """apply body force

        Args:
            v: test function

        Returns: form for body load

        """
        force_vector = np.zeros(self.p["dim"])
        force_vector[-1] = -self.p["rho"] * self.p["g"]

        f = df.fem.Constant(self.mesh, ScalarType(force_vector))
        L = ufl.dot(f, v) * ufl.dx

        return L

    def boundary_bottom(self) -> Callable:
        """specify boundary: plane at bottom

        Returns: fct defining if dof is at boundary

        """
        if self.p["dim"] == 2:
            return plane_at(0.0, "y")
        elif self.p["dim"] == 3:
            return plane_at(0.0, "z")
