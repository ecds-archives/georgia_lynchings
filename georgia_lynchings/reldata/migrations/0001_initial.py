# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Relationship'
        db.create_table('reldata_relationship', (
            ('subject_exact_age', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('subject_race', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('object_gender', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_reason', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('subject_first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('subject_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('subject_adjective', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('process_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('subject_gender', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_city', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('object_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('object_race', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('subject_age_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('triplet_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('process_instrument', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal('reldata', ['Relationship'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Relationship'
        db.delete_table('reldata_relationship')
    
    
    models = {
        'reldata.relationship': {
            'Meta': {'object_name': 'Relationship'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_desc': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'object_gender': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'object_race': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'process_city': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'process_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'process_desc': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'process_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'process_instrument': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'process_reason': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'subject_adjective': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'subject_age_desc': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_desc': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_exact_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject_first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_gender': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'subject_last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_race': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'triplet_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        }
    }
    
    complete_apps = ['reldata']
