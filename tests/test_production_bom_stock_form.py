# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
import doctest
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from decimal import Decimal
from functools import partial
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.modules.company.tests import create_company, set_company


class ProductionBomStockFormTestCase(ModuleTestCase):
    'Test Production Bom Stock Form module'
    module = 'production_bom_stock_form'

    @with_transaction()
    def setUp(self):
        pool = Pool()
        self.template = pool.get('product.template')
        self.product = pool.get('product.product')
        self.category = pool.get('product.category')
        self.uom = pool.get('product.uom')
        self.location = pool.get('stock.location')
        self.bom = pool.get('production.bom')
        self.bom_imput = pool.get('production.bom.input')
        self.bom_output = pool.get('production.bom.output')
        self.bom_tree = pool.get('production.bom.tree.open.tree')
        self.product_bom = pool.get('product.product-production.bom')
        self.inventory = pool.get('stock.inventory')
        self.inventory_line = pool.get('stock.inventory.line')
        self.move = pool.get('stock.move')
        self.company = pool.get('company.company')
        self.user = pool.get('res.user')
        self.production = pool.get('production')


    @with_transaction()
    def test0010production_bom_tree(self):
        'Test production BOM tree'
        category, = self.category.create([{
                    'name': 'Test Production BOM Tree',
                    }])
        uom, = self.uom.search([('name', '=', 'Unit')])

        company = create_company()
        template, = self.template.create([{
                    'name': 'Product',
                    'type': 'goods',
                    'list_price': Decimal(0),
                    'producible': True,
                    # 'category': category.id,
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
                    # 'category': category.id,
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
                    # 'category': category.id,
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

        # currency = company.currency
        # self.user.write([self.user(USER)], {
        #     'main_company': company.id,
        #     'company': company.id,
        #     })

        today = datetime.date.today()
        with set_company(company):

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
            with Transaction().set_context(locations=[warehouse_loc.id],
                    stock_date_end=today):
                bom_trees = tree()
                for bom_tree in bom_trees:
                    results = bom_trees[bom_tree]
                    for result in results:
                        for key in result:
                            if 'rec_name' in key:
                                continue
                            if key != 'childs':
                                self.assertEqual(result[key],
                                    test_product[key])
                            else:
                                for child in result[key]:
                                    for child_key in child:
                                        if 'rec_name' in child_key:
                                            continue
                                        if 'childs' == child_key:
                                            continue
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
                        # 'currency': currency.id,
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
                        # 'currency': currency,
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
                        # 'currency': currency,
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
                        # 'currency': currency,
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
            with Transaction().set_context(locations=[warehouse_loc.id],
                    stock_date_end=today):
                bom_trees = tree()
                for bom_tree in bom_trees:
                    results = bom_trees[bom_tree]
                    for result in results:
                        for key in result:
                            if 'rec_name' in key:
                                continue
                            if key != 'childs':
                                self.assertEqual(result[key],
                                    test_product[key])
                            else:
                                for child in result[key]:
                                    for child_key in child:
                                        if 'rec_name' in child_key:
                                            continue
                                        if 'childs' == child_key:
                                            continue
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
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        ProductionBomStockFormTestCase))
    return suite
