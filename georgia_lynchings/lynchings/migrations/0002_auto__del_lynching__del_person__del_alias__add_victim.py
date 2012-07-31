# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'Lynching'
        db.delete_table('lynchings_lynching')

        # Removing M2M table for field alternate_counties on 'Lynching'
        db.delete_table('lynchings_lynching_alternate_counties')

        # Deleting model 'Person'
        db.delete_table('lynchings_person')

        # Deleting model 'Alias'
        db.delete_table('lynchings_alias')

        # Adding model 'Victim'
        db.create_table('lynchings_victim', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('detailed_reason', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['demographics.County'], null=True, blank=True)),
            ('race', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Race'], null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('lynchings', ['Victim'])

        # Adding M2M table for field accusation on 'Victim'
        db.create_table('lynchings_victim_accusation', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('victim', models.ForeignKey(orm['lynchings.victim'], null=False)),
            ('accusation', models.ForeignKey(orm['lynchings.accusation'], null=False))
        ))
        db.create_unique('lynchings_victim_accusation', ['victim_id', 'accusation_id'])
    
    
    def backwards(self, orm):
        
        # Adding model 'Lynching'
        db.create_table('lynchings_lynching', (
            ('story', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Story'])),
            ('pca_last_update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pca_id', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, db_index=True)),
            ('county', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['demographics.County'], null=True, blank=True)),
            ('alleged_crime', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Accusation'], null=True, blank=True)),
            ('victim', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['lynchings.Person'], unique=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('lynchings', ['Lynching'])

        # Adding M2M table for field alternate_counties on 'Lynching'
        db.create_table('lynchings_lynching_alternate_counties', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lynching', models.ForeignKey(orm['lynchings.lynching'], null=False)),
            ('county', models.ForeignKey(orm['demographics.county'], null=False))
        ))
        db.create_unique('lynchings_lynching_alternate_counties', ['lynching_id', 'county_id'])

        # Adding model 'Person'
        db.create_table('lynchings_person', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True)),
            ('pca_id', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, db_index=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('age', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('race', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Race'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pca_last_update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('lynchings', ['Person'])

        # Adding model 'Alias'
        db.create_table('lynchings_alias', (
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Person'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75)),
        ))
        db.send_create_signal('lynchings', ['Alias'])

        # Deleting model 'Victim'
        db.delete_table('lynchings_victim')

        # Removing M2M table for field accusation on 'Victim'
        db.delete_table('lynchings_victim_accusation')
    
    
    models = {
        'articles.article': {
            'Meta': {'object_name': 'Article'},
            'contributor': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'coverage': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
        },
        'lynchings.victim': {
            'Meta': {'object_name': 'Victim'},
            'accusation': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['lynchings.Accusation']", 'null': 'True', 'blank': 'True'}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['demographics.County']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'detailed_reason': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'race': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lynchings.Race']", 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['lynchings']
