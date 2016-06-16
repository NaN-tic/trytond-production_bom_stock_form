# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .production import *


def register():
    Pool.register(
        BOMTree,
        OpenBOMTreeStart,
        OpenBOMTreeTree,
        module='production_bom_stock_form', type_='model')
    Pool.register(
        OpenBOMTree,
        module='production_bom_stock_form', type_='wizard')
