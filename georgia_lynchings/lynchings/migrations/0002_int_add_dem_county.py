# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding field 'Lynching.d_county'
        db.add_column('lynchings_lynching', 'd_county', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['demographics.County'], null=True, blank=True), keep_default=False)

        # Adding M2M table for field d_alt_counties on 'Lynching'
        db.create_table('lynchings_lynching_d_alt_counties', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lynching', models.ForeignKey(orm['lynchings.lynching'], null=False)),
            ('county', models.ForeignKey(orm['demographics.county'], null=False))
        ))
        db.create_unique('lynchings_lynching_d_alt_counties', ['lynching_id', 'county_id'])
    
    
    def backwards(self, orm):
        
        # Deleting field 'Lynching.d_county'
        db.delete_column('lynchings_lynching', 'd_county_id')

        # Removing M2M table for field d_alt_counties on 'Lynching'
        db.delete_table('lynchings_lynching_d_alt_counties')
    
    
    models = {
        'articles.article': {
            'Meta': {'object_name': 'Article'},
            'contributor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'coverage': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'EN'", 'max_length': '2'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'relation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'rights': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '2'})
        },
        'demographics.county': {
            'Meta': {'object_name': 'County'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'lynchings.accusation': {
            'Meta': {'object_name': 'Accusation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '75'})
        },
        'lynchings.alias': {
            'Meta': {'object_name': 'Alias'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.Person']"})
        },
        'lynchings.county': {
            'Meta': {'object_name': 'County'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {})
        },
        'lynchings.lynching': {
            'Meta': {'object_name': 'Lynching'},
            'alleged_crime': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.Accusation']", 'null': 'True', 'blank': 'True'}),
            'alternate_counties': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'alt_counties'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['lynchings.County']"}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.County']", 'null': 'True', 'blank': 'True'}),
            'd_alt_counties': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'alt_counties'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['demographics.County']"}),
            'd_county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demographics.County']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pca_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'pca_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'story': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.Story']"}),
            'victim': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['lynchings.Person']", 'unique': 'True'})
        },
        'lynchings.person': {
            'Meta': {'object_name': 'Person'},
            'age': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'pca_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'pca_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'race': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.Race']", 'null': 'True', 'blank': 'True'})
        },
        'lynchings.race': {
            'Meta': {'object_name': 'Race'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'lynchings.story': {
            'Meta': {'object_name': 'Story'},
            'articles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['articles.Article']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pca_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'pca_last_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['lynchings']
