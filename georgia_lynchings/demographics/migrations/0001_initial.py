# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'County'
        db.create_table('demographics_county', (
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('demographics', ['County'])

        # Adding model 'Population'
        db.create_table('demographics_population', (
            ('iltr_black', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['demographics.County'])),
            ('iltr_white', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('black', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('white', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('demographics', ['Population'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'County'
        db.delete_table('demographics_county')

        # Deleting model 'Population'
        db.delete_table('demographics_population')
    
    
    models = {
        'demographics.county': {
            'Meta': {'object_name': 'County'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'demographics.population': {
            'Meta': {'object_name': 'Population'},
            'black': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demographics.County']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iltr_black': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'iltr_white': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'white': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }
    
    complete_apps = ['demographics']
