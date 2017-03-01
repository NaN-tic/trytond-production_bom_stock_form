# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
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

        if Transaction().context.get('show_stock', True):
            product = Product(bom_tree['product'])

            input_stock = cls.get_input_output_product(
                [product], 'input_stock')[product.id]
            output_stock = cls.get_input_output_product(
                [product], 'output_stock')[product.id]
            quantity = product.quantity
        else:
            input_stock = None
            output_stock = None
            quantity = None

        bom_tree['input_stock'] = input_stock
        bom_tree['output_stock'] = output_stock
        bom_tree['current_stock'] = quantity

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
    show_stock = fields.Boolean('Show stock',
        help='Show stock quantity')
    date = fields.Date('Date',
        states={
            'required': Eval('show_stock', False),
            'invisible': ~Eval('show_stock', False),
        }, depends=['show_stock'],
        help='The date that calculate stock quantity')
    warehouse = fields.Many2One('stock.location', 'Warehouse',
        domain=[
            ('type', '=', 'warehouse'),
        ], states={
            'required': Eval('show_stock', False),
            'invisible': ~Eval('show_stock', False),
        }, depends=['show_stock'],
        help='The warehouse that calculate stock quantity')

    @staticmethod
    def default_show_stock():
        return True


class OpenBOMTreeTree(StockMixin):
    __metaclass__ = PoolMeta
    __name__ = 'production.bom.tree.open.tree'

    @classmethod
    def tree(cls, bom, product, quantity, uom):
        Product = Pool().get('product.product')

        bom_tree = super(OpenBOMTreeTree, cls).tree(
            bom, product, quantity, uom)

        if Transaction().context.get('show_stock', True):
            product = Product(bom_tree['bom_tree'][0]['product'])

            input_stock = cls.get_input_output_product(
                [product], 'input_stock')[product.id]
            output_stock = cls.get_input_output_product(
                [product], 'output_stock')[product.id]
            quantity = product.quantity
        else:
            input_stock = None
            output_stock = None
            quantity = None

        bom_tree['bom_tree'][0]['input_stock'] = input_stock
        bom_tree['bom_tree'][0]['output_stock'] = output_stock
        bom_tree['bom_tree'][0]['current_stock'] = quantity

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
        context = {'show_stock': self.start.show_stock}
        if self.start.date:
            context['stock_date_end'] = self.start.date
        if self.start.warehouse:
            context['locations'] = [self.start.warehouse.id]

        with Transaction().set_context(**context):
            return super(OpenBOMTree, self).default_tree(fields)
