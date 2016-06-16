# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.stock_calculation import StockMixin


__all__ = ['BOMTree', 'OpenBOMTreeStart', 'OpenBOMTreeTree', 'OpenBOMTree']


class BOMTree(StockMixin):
    __metaclass__ = PoolMeta
    __name__ = 'production.bom.tree'
    input_stock = fields.Float('Inputs')
    output_stock = fields.Float('Outputs')
    current_stock = fields.Float('Current Stock')

    @classmethod
    def set_stock_recursively(cls, bom_tree):
        Product = Pool().get('product.product')
        product = Product(bom_tree['product'])
        bom_tree['input_stock'] = cls.get_input_output_stock([product],
            'input_stock')[product.id]
        bom_tree['output_stock'] = cls.get_input_output_stock([product],
            'output_stock')[product.id]
        bom_tree['current_stock'] = product.quantity
        if bom_tree['childs']:
            for child in bom_tree['childs']:
                cls.set_stock_recursively(child)

    @classmethod
    def tree(cls, product, quantity, uom, bom=None):
        bom_trees = super(BOMTree, cls).tree(product, quantity, uom, bom)
        for bom_tree in bom_trees:
            cls.set_stock_recursively(bom_tree)
        return bom_trees


class OpenBOMTreeStart:
    __metaclass__ = PoolMeta
    __name__ = 'production.bom.tree.open.start'
    date = fields.Date('Date', required=True)
    warehouse = fields.Many2One('stock.location', 'Warehouse', required=True,
        domain=[
            ('type', '=', 'warehouse'),
            ])


class OpenBOMTreeTree(StockMixin):
    __metaclass__ = PoolMeta
    __name__ = 'production.bom.tree.open.tree'

    @classmethod
    def tree(cls, bom, product, quantity, uom):
        Product = Pool().get('product.product')

        bom_tree = super(OpenBOMTreeTree, cls).tree(bom, product, quantity,
            uom)

        product = Product(bom_tree['bom_tree'][0]['product'])
        bom_tree['bom_tree'][0]['input_stock'] = cls.get_input_output_stock(
            [product], 'input_stock')[product.id]
        bom_tree['bom_tree'][0]['output_stock'] = cls.get_input_output_stock(
            [product], 'output_stock')[product.id]
        bom_tree['bom_tree'][0]['current_stock'] = product.quantity
        return bom_tree


class OpenBOMTree:
    __metaclass__ = PoolMeta
    __name__ = 'production.bom.tree.open'

    def default_start(self, fields):
        Date = Pool().get('ir.date')
        defaults = super(OpenBOMTree, self).default_start(fields)
        defaults['date'] = Date.today()
        return defaults

    def default_tree(self, fields):
        with Transaction().set_context(stock_date_end=self.start.date,
                locations=[self.start.warehouse.id]):
            return super(OpenBOMTree, self).default_tree(fields)
