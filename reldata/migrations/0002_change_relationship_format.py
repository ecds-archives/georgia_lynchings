# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'Relationship'
        db.delete_table('reldata_relationship')

        # Adding model 'Relation'
        db.create_table('reldata_relation', (
            ('event_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('story_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('object', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='relations_as_object', null=True, to=orm['reldata.Actor'])),
            ('sequence_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('action', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reldata.Action'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('triplet_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='relations_as_subject', null=True, to=orm['reldata.Actor'])),
        ))
        db.send_create_signal('reldata', ['Relation'])

        # Adding model 'Actor'
        db.create_table('reldata_actor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
        ))
        db.send_create_signal('reldata', ['Actor'])

        # Adding model 'Action'
        db.create_table('reldata_action', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=80)),
        ))
        db.send_create_signal('reldata', ['Action'])
    
    
    def backwards(self, orm):
        
        # Adding model 'Relationship'
        db.create_table('reldata_relationship', (
            ('process_reason', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
            ('subject_first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('story', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lynchings.Story'], null=True, blank=True)),
            ('subject_race', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_id', self.gf('django.db.models.fields.PositiveIntegerField')(blank=True, null=True, db_index=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(blank=True, null=True, db_index=True)),
            ('process_city', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('object_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_gender', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('process_id', self.gf('django.db.models.fields.PositiveIntegerField')(blank=True, null=True, db_index=True)),
            ('object_gender', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_age_desc', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('triplet_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('process_instrument', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_exact_age', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('object_race', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('subject_adjective', self.gf('django.db.models.fields.CharField')(max_length=60, blank=True)),
        ))
        db.send_create_signal('reldata', ['Relationship'])

        # Deleting model 'Relation'
        db.delete_table('reldata_relation')

        # Deleting model 'Actor'
        db.delete_table('reldata_actor')

        # Deleting model 'Action'
        db.delete_table('reldata_action')
    
    
    models = {
        'reldata.action': {
            'Meta': {'object_name': 'Action'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'reldata.actor': {
            'Meta': {'object_name': 'Actor'},
            'description': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'reldata.relation': {
            'Meta': {'object_name': 'Relation'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reldata.Action']", 'null': 'True', 'blank': 'True'}),
            'event_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'relations_as_object'", 'null': 'True', 'to': "orm['reldata.Actor']"}),
            'sequence_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'story_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'relations_as_subject'", 'null': 'True', 'to': "orm['reldata.Actor']"}),
            'triplet_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }
    
    complete_apps = ['reldata']
