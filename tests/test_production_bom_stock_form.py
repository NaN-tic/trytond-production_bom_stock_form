# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import doctest
import trytond.tests.test_tryton
import unittest
from decimal import Decimal
from functools import partial
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('production_bom_stock_form')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.category = POOL.get('product.category')
        self.uom = POOL.get('product.uom')
        self.location = POOL.get('stock.location')
        self.bom = POOL.get('production.bom')
        self.bom_imput = POOL.get('production.bom.input')
        self.bom_output = POOL.get('production.bom.output')
        self.bom_tree = POOL.get('production.bom.tree.open.tree')
        self.product_bom = POOL.get('product.product-production.bom')
        self.inventory = POOL.get('stock.inventory')
        self.inventory_line = POOL.get('stock.inventory.line')
        self.move = POOL.get('stock.move')
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')
        self.production = POOL.get('production')

    def test0005views(self):
        'Test views'
        test_view('production_bom_stock_form')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010production_bom_tree(self):
        'Test production BOM tree'
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            category, = self.category.create([{
                        'name': 'Test Production BOM Tree',
                        }])
            uom, = self.uom.search([('name', '=', 'Unit')])

            template, = self.template.create([{
                        'name': 'Product',
                        'type': 'goods',
                        'list_price': Decimal(0),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': uom.id,
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])

            template1, = self.template.create([{
                        'name': 'Component 1',
                        'type': 'goods',
                        'list_price': Decimal(0),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': uom.id,
                        }])
            component1, = self.product.create([{
                        'template': template.id,
                        }])

            template2, = self.template.create([{
                        'name': 'Component 2',
                        'type': 'goods',
                        'list_price': Decimal(0),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': uom.id,
                        }])
            component2, = self.product.create([{
                        'template': template.id,
                        }])

            warehouse_loc, = self.location.search([('code', '=', 'WH')])
            supplier_loc, = self.location.search([('code', '=', 'SUP')])
            input_loc, = self.location.search([('code', '=', 'IN')])
            customer_loc, = self.location.search([('code', '=', 'CUS')])
            storage_loc, = self.location.search([('code', '=', 'STO')])
            output_loc, = self.location.search([('code', '=', 'OUT')])
            production_loc, = self.location.search([('code', '=', 'PROD')])

            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            currency = company.currency
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            today = datetime.date.today()

            bom, = self.bom.create([{
                        'name': 'Product',
                        }])
            self.bom_output.create([{
                        'product': product,
                        'quantity': 1,
                        'bom': bom,
                        'uom': uom,
                        }])
            self.bom_imput.create([{
                        'product': component1,
                        'quantity': 5,
                        'bom': bom,
                        'uom': uom,
                        }])
            self.bom_imput.create([{
                        'product': component2,
                        'quantity': 20,
                        'bom': bom,
                        'uom': uom,
                        }])
            self.product_bom.create([{
                        'bom': bom,
                        'product': product,
                        }])
            inventory, = self.inventory.create([{
                        'company': company.id,
                        'location': storage_loc.id,
                        }])
            self.inventory_line.create([{
                        'product': component1,
                        'quantity': 10,
                        'inventory': inventory,
                        }])
            self.inventory_line.create([{
                        'product': component2,
                        'quantity': 20,
                        'inventory': inventory,
                        }])
            self.inventory.confirm([inventory])

            tree = partial(self.bom_tree.tree, bom, product, 1, uom)

            test_product = {
                'product': product.id,
                'quantity': 1,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 0,
                'output_stock': 0,
                'current_stock': 0.0,
                }
            test_component1 = {
                'product': component1.id,
                'quantity': 5.0,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 0,
                'output_stock': 0,
                'current_stock': 10.0,
                'childs': [],
                }
            test_component2 = {
                'product': component2.id,
                'quantity': 20.0,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 0,
                'output_stock': 0,
                'current_stock': 20.0,
                'childs': [],
                }
            with transaction.set_context(locations=[warehouse_loc.id],
                    stock_date_end=today):
                bom_trees = tree()
                for bom_tree in bom_trees:
                    results = bom_trees[bom_tree]
                    for result in results:
                        for key in result:
                            if key != 'childs':
                                self.assertEqual(result[key],
                                    test_product[key])
                            else:
                                for child in result[key]:
                                    for child_key in child:
                                        if child['product'] == component1.id:
                                            self.assertEqual(child[child_key],
                                                test_component1[child_key])
                                        else:
                                            self.assertEqual(child[child_key],
                                                test_component2[child_key])

            in_move, = self.move.create([{
                        'product': component1.id,
                        'uom': uom.id,
                        'quantity': 5,
                        'from_location': supplier_loc.id,
                        'to_location': input_loc.id,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }])

            production, = self.production.create([{
                        'product': product,
                        'bom': bom,
                        'quantity': 1,
                        'location': production_loc.id,
                        'warehouse': warehouse_loc.id,
                        'company': company.id,
                        'uom': uom.id,
                        }])
            self.move.create([{
                        'product': product,
                        'uom': uom,
                        'quantity': 1,
                        'from_location': production_loc,
                        'to_location': storage_loc,
                        'effective_date': today,
                        'company': company,
                        'unit_price': Decimal('1'),
                        'currency': currency,
                        'production_output': production,
                        }])
            self.move.create([{
                        'product': component1,
                        'uom': uom,
                        'quantity': 5,
                        'from_location': storage_loc,
                        'to_location': production_loc,
                        'effective_date': today,
                        'company': company,
                        'unit_price': Decimal('1'),
                        'currency': currency,
                        'production_input': production,
                        }])
            self.move.create([{
                        'product': component2,
                        'uom': uom,
                        'quantity': 20,
                        'from_location': storage_loc,
                        'to_location': production_loc,
                        'effective_date': today,
                        'company': company,
                        'unit_price': Decimal('1'),
                        'currency': currency,
                        'production_input': production,
                        }])
            self.production.wait([production])
            self.production.assign_try([production])
            test_product = {
                'product': product.id,
                'quantity': 1,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 0,
                'output_stock': 0,
                'current_stock': 0.0,
                }
            test_component1 = {
                'product': component1.id,
                'quantity': 5.0,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 5.0,
                'output_stock': 5,
                'current_stock': 10.0,
                'childs': [],
                }
            test_component2 = {
                'product': component2.id,
                'quantity': 20.0,
                'uom': uom.id,
                'unit_digits': uom.digits,
                'input_stock': 0,
                'output_stock': 20,
                'current_stock': 20.0,
                'childs': [],
                }
            with transaction.set_context(locations=[warehouse_loc.id],
                    stock_date_end=today):
                bom_trees = tree()
                for bom_tree in bom_trees:
                    results = bom_trees[bom_tree]
                    for result in results:
                        for key in result:
                            if key != 'childs':
                                self.assertEqual(result[key],
                                    test_product[key])
                            else:
                                for child in result[key]:
                                    for child_key in child:
                                        if child['product'] == component1.id:
                                            self.assertEqual(child[child_key],
                                                test_component1[child_key])
                                        else:
                                            self.assertEqual(child[child_key],
                                                test_component2[child_key])


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
