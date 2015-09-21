# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment
import threading


class service_equi_operation(models.TransientModel):
    _name = 'service.equi.operation'
    _inherits = {'service.enter.reading': 'enter_reading_id'}
    _description = "Service Equipment Operation"


    enter_reading_id = fields.Many2one('service.enter.reading', string='Enter Reading', required=True, ondelete="cascade") 
    state = fields.Selection( [('ins','Installation'),('ebk','Enable backup'), ('dbk','Disable backup'), ('rem','Removal') ], string='Operation', default='ins', readonly=True )  
    equipment_id = fields.Many2one('service.equipment', string="Equipment", readonly=True)
    
    equipment_backup_id = fields.Many2one('service.equipment', string="Backup Equipment",domain=[('state','=','available')])
    
    partner_id = fields.Many2one('res.partner', string='Owner',domain=[('is_company','=',True)])
    address_id = fields.Many2one('res.partner', string='Location',domain=[('type','in',['default','other'])]) # sa fac un nou tip de partener? locatie ?
    emplacement = fields.Char(string='Emplacement')    


    @api.model
    def default_get(self, fields):
        defaults = super(service_equi_operation, self).default_get(fields)
      
        active_id = self.env.context.get('active_id', False)
        if active_id:
            defaults['equipment_id'] =  active_id
        else:
            raise Warning(_('Please select equipment.'))
        return defaults


    @api.onchange('equipment_backup_id','date')
    def onchange_equipment_backup_id(self):
        items = []
        for meter in self.equipment_id.meter_ids:
            meter = meter.with_context({'date':self.date})
            items += [(0,0,{'meter_id':meter.id,
                            'equipment_id':meter.equipment_id.id,
                             'counter_value':meter.estimated_value})]
            
        
        if self.equipment_backup_id:
            for meter in self.equipment_backup_id.meter_ids:
                meter = meter.with_context({'date':self.date})
                items += [(0,0,{'meter_id':meter.id,
                                'equipment_id':meter.equipment_id.id,
                                 'counter_value':meter.estimated_value})]
                

        items =  self._convert_to_cache({'items': items }, validate=False)
        self.update(items) 

    @api.multi    
    def do_operation(self):
        
        if self.equipment_id.equipment_history_id:
            if self.date < self.equipment_id.equipment_history_id.from_date:
                raise Warning(_('Date must be greater than %s') % self.equipment_id.equipment_history_id.from_date)

        values =   {'equipment_id':self.equipment_id.id,
                    'from_date': self.date,
                    'partner_id':self.partner_id.id,
                    'address_id':self.address_id.id,
                    'emplacement':self.emplacement,                                                               
                    }   
        
        if self.state == 'ebk':
            values['equipment_backup_id'] = equipment_backup_id.id
            
        new_hist = self.env['service.equipment.history'].create(values)
        
 
        
        if self.stare == 'ins':
            self.equipment_id.write({'equipment_history_id':new_hist.id,'state':'installed'})     
        elif self.stare == 'rem':
            self.equipment_id.write({'equipment_history_id':new_hist.id,'state':'available'})      
        elif self.stare == 'ebk':
            self.equipment_id.write({'equipment_history_id':new_hist.id,'state':'backuped'})   
            values['equipment_id'] = equipment_backup_id.id
            new_hist = self.env['service.equipment.history'].create(values)
            self.equipment_backup_id.write({'state':'installed','equipment_history_id':new_hist.id}) 
        elif self.stare == 'dbk':
            self.equipment_id.write({'equipment_history_id':new_hist.id,'state':'installed'})
            values =   {'equipment_id':self.equipment_backup_id.id,
                    'from_date': self.date,
                    'partner_id':False,
                    'address_id':False,
                    'emplacement':False,                                                               
                    }  
            new_hist = self.env['service.equipment.history'].create(values)
            self.equipment_backup_id.write({'state':'available','equipment_history_id':new_hist.id})    
            

                    
        
        self.do_enter()  # enter readings
        return

       

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    