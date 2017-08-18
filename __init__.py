# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import production


def register():
    Pool.register(
        production.BOMTree,
        production.OpenBOMTreeStart,
        production.OpenBOMTreeTree,
        module='production_bom_stock_form', type_='model')
    Pool.register(
        production.OpenBOMTree,
        module='production_bom_stock_form', type_='wizard')
