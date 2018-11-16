#!/usr/bin/python3
# import sys
import os
# import csv
# import sqlite3
import pickle
# import remi.gui as gui

from Expr_Table_Def import lang_uid_col, lang_name_col, comm_uid_col, comm_name_col, \
    lh_uid_col, lh_name_col, lh_role_uid_col, lh_role_name_col, idea_uid_col, \
    rel_type_uid_col, phrase_type_uid_col, rh_role_uid_col, rh_role_name_col, \
    rh_uid_col, rh_name_col, part_def_col, uom_uid_col, uom_name_col
#   intent_uid_col, intent_name_col, rel_type_name_col, full_def_col, status_col
from Gellish_file import Gellish_file
from Anything import Anything, Relation
from Bootstrapping import boot_base_phrasesEN, boot_base_phrasesNL, \
    boot_inverse_phrasesEN, boot_inverse_phrasesNL, boot_alias_uids, \
    basePhraseUID, inversePhraseUID, binRelUID, classifUID, classifiedUID, \
    indOrMixRelUID, indivRelUID, kindHierUID, kindKindUID, kindRelUID, mixedRelUID, \
    specialRelUID, possAspUID, possessorUID, transRelUID, concPossAspUID, \
    concComplRelUID, qualSubtypeUID, qualOptionsUID, concComplUID, concQuantUID, \
    qualifUID, quantUID, informativeUID, occurrenceUID, composUID, componUID, \
    concComposUID, concComponUID, involvUID, nextUID, shallUID, aliasUID, \
    concWholeUID, concPosessorUID, transUID, specialUID, concBinRelKindsUID, \
    kindAndMixRelUID, \
    first_role_uid, second_role_uid, base_rel_type_uids, \
    is_called_uid, by_def_role_of_ind, subtypeRoleUID, Dutch_uid, \
    dict_file_names, dict_dirs, model_file_names, model_dirs, prod_file_names, prod_dirs, \
    base_onto_file_name
from GellishDict import GellishDict
from Create_output_file import Convert_numeric_to_integer, Message


class Semantic_Network():
    ''' Build and query a Semantic_Network model.
        Build the network from Gellish expressions read in Expression_list.
        Every node in the network is an instance of Anything.
        Every binary relation is an instance of Relation which is a subtype of Anything.
        dictionary = instance of Gel_dict = naming dictionary that is built from
        the concepts (including relations) and their names and synonyms in the network.
        Start initially with bootstrapping base relation types,
              base_phrases being bootstrapping base phrases for binary relations
              and inverse_phrases being bootstrapping inverse phrases.
    '''
    def __init__(self, GUI_lang_index, net_name):
        ''' Initialize a semantic network based on import of Gellish files.'''
        self.GUI_lang_index = GUI_lang_index
        self.name = net_name
        self.semantic_file_name = "Gellish_net_db"

        self.Gellish_files = []
        self.rels = []
        self.idea_uids = []
        self.rel_types = []  # initialize and collect all binary relation types
        #                      (being 'binary relation' and its subtypes)
        self.rel_type_uids = base_rel_type_uids
        self.uid_dict = {}   # key = uid; value = obj (an instance of Anything)
        # self.rel_uid_dict = {}  # key = uid; value = binary relation (an instance of Anything)
        self.objects = []
        self.undefined_objects = []
        self.languages = []
        # A dictionary for names in a context that refers to the denoted concepts
        self.dictionary = GellishDict('Dictionary of Gellish formal languages')

        self.lang_uid_dict = {}
        self.community_dict = {}
        self.lang_dict_EN = {'910036': "English",
                             '910037': "Dutch",
                             '589211': "international",
                             '910038': "German",
                             '910039': "French",
                             '911689': "American"}
        self.lang_dict_NL = {'910036': "Engels",
                             '910037': "Nederlands",
                             '589211': "internationaal",
                             '910038': "Duits",
                             '910039': "Frans",
                             '911689': "Amerikaans"}
        self.comm_dict_EN = {'492014': "Gellish"}
        self.comm_dict_NL = {'492014': "Gellish"}

        self.total_base_phrases = boot_base_phrasesEN + boot_base_phrasesNL
        self.total_inverse_phrases = boot_inverse_phrasesEN + boot_inverse_phrasesNL
        # UIDs that define a taxonomy: subtypes of 1146: the base UID for 'is a kind of'
        self.specialRelUIDs = ['1146', '1726', '5277', '6022', '5396', '5683']
        # Some UIDs that are classification relations, being subtypes of 1225:
        self.classifUIDs = ['1225', '1588']   # 1225 base UID for 'is classified as a'
#        UIDs that imply a new UoM in units and currencies table.
#        uom_def_uids = ['1726', '5708', '1981']
        self.subComposUIDs = []
        self.subConcComposUIDs = []
        self.alias_uids = boot_alias_uids
        # self.allBinRel_types = []  # initialize and collect all binary relation types
        #                              (being 'binary relation' and its subtypes)
        self.new_obj_uid = 100  # default start UID for new things in model mappings
        self.new_things = {}   # collection of new things in model mappings
        self.new_idea_uid = 500  # default start UID for unknown relations in model mappings
        self.select_dict = {}
        self.base_ontology = False

        # Intialize list of [uid, name, description] of candidates for mapping
        self.uid_name_desc_list = []

        self.nameless = ['nameless', 'naamloos', '']
        self.categories_of_kinds = ['kind', 'kind of physical object',
                                    'kind of occurrence',
                                    'kind of aspect', 'kind of role',
                                    'kind of relation', 'qualitative kind']
        self.non_object = Anything('', '')

    def reset_network(self, net_name):
        ''' Reset the network properties to their initial values.'''
        self.__init__(net_name)

    def reset_and_build_network(self):
        ''' Reset the network and build a new content.'''
        self.reset_network('Gellish semantic network')
        self.build_network

    def build_network(self):
        ''' Build a new semantic network
            by bootstrapping kinds of relations
            and read and process the language definition files.
        '''
        # Create a base dictionary of kinds of relations
        # from the list in the bootstrapping module
        self.Create_base_reltype_objects()

        # Build a new network from files
        # that contain a language definition
        # and store the content of the files in the database
        self.Build_new_network()
        print("Network '{}' is built.".format(self.name))

    def Build_new_network(self):
        ''' Build network from files as specified in Bootstrapping.py:
            First read a base ontology from a file
            Then read UoMs and other dictionary files, knowledge files and model files
        '''
        # Read base ontology (base language definition) from Gellish file
        # and build base semantic network
        self.Import_Base_Ontology()

        # Verify base semantic network and collect rel_types for validation
        self.Verify_Base_Semantic_Network()

        # Import domain dictionaries from files
        # (as specified in Bootstrapping module)
        self.Import_Model_Files(dict_file_names, dict_dirs)

        # Import knowledge, requirements and product_type models
        # (as specified in Bootstrapping)
        if len(model_file_names) > 0:
            self.Import_Model_Files(model_file_names, model_dirs)

        # Import product and process models in db from files
        # (specified in Bootstrapping module)
        # and extend the network with domain dictionaries and product models (if any)
        if len(prod_file_names) > 0:
            self.Import_Model_Files(prod_file_names, prod_dirs)

        self.Verify_network()

    def Import_Base_Ontology(self):
        ''' Read a base ontology CSV file and
            import its content and build the base semantic network.
            The base_onto_path is specified in the bootstrapping module.
        '''
        # Build file path_and_name from list of dirs and file name
        # that are specified in the bootstrapping module
        onto_file_path = []
        dirs = dict_dirs[:]
        for dir in dirs:
            onto_file_path.append(dir)
        onto_file_path.append(base_onto_file_name)
        onto_path = os.path.join(*onto_file_path)
        print('Ontology path:', onto_path)

        # Create file object
        self.current_file = Gellish_file(onto_path, self)
        self.Gellish_files.append(self.current_file)

        self.current_file.Import_Gellish_from_file()
        # Debug print('Imported: base ontology')

    def Import_Model_Files(self, file_names, model_dirs):
        ''' Read models in CSV file(s) as specified in the bootstrapping module
            and import their content in the semantic network.
        '''
        # Create list of files with their paths, names and extensions
        for file_name in file_names:
            # Build path and name from list of dirs and name
            path_and_name = []
            dirs = model_dirs[:]
            for dir in dirs:
                path_and_name.append(dir)
            path_and_name.append(file_name)
            model_path = os.path.join(*path_and_name)
            self.current_file = Gellish_file(model_path, self)
            self.Gellish_files.append(self.current_file)
            # Debug print('Model file: ', self.current_file.path_and_name)

            # Read the file and import its content in the semantic network
            self.current_file.Import_Gellish_from_file()

    def Create_base_reltype_objects(self):
        ''' Create initial collection of relation_type objects
            conform Bootstrapping base_rel_type_uids.
            Ans add them to the list of relation types and to the uid dictionary.
        '''
        for rel_type_uid in base_rel_type_uids:
            rel_type_name = base_rel_type_uids[rel_type_uid]
            rel_type = Anything(rel_type_uid, rel_type_name, 'kind of relation')
            self.rel_types.append(rel_type)
            self.uid_dict[rel_type_uid] = rel_type
            # self.rel_uid_dict[rel_type_uid] = rel_type

    def Verify_Base_Semantic_Network(self):
        ''' Verify and complete the base Semantic Network
            that is built from an initial 'base_ontology' definition in a file in Gellish.
            Determine the list of kinds of binary relations (subtypes of 'binary relation').
            Then complete and verify the base semantic network.
        '''
        # Complete and Verify base semantic network
        # Determine all subtypes of binary relation (5935)
        # and first_roles and second_roles and role players for all subtypes of binary relation
        # thus extending the list of kinds of relations, base phrases and inverse phrases

        kind_rel = self.uid_dict[binRelUID]  # uid = 5935
        kind_rel.category = 'kind of relation'

        # Determine list of all subtypes of binary relation (5935)
        # and specify their self.category as 'kind of relation'
        # and determine their first and second kind of role (self.first_role and self.second_role)
        self.rel_types, self.rel_type_uids = self.Determine_subtype_list(binRelUID)
        Message(self.GUI_lang_index,
                'Base network: {} contains {} objects and {} relations and {} kinds of relations.'.
                format(self.name, len(self.objects), len(self.rels), len(self.rel_type_uids)),
                'Basisnetwerk: {} bevat {} objecten en {} relaties en {} soorten relaties.'.
                format(self.name, len(self.objects), len(self.rels), len(self.rel_type_uids)))

        # Check whether each concept has at least one supertype concept
        # (except for anything = 730000)
        for obj in self.objects:
            if obj.category in ['kind', 'kind of physical object',
                                'kind of occurrence', 'kind of aspect',
                                'kind of role', 'kind of relation']:
                if len(obj.supertypes) == 0 and obj.uid != '730000':
                    Message(self.GUI_lang_index,
                            'Kind ({}) {} in the base ontology has no supertype(s).'.
                            format(obj.uid, obj.name),
                            'Soort ({}) {} in de basisontologie heeft geen supertype(s).'.
                            format(obj.uid, obj.name))

        # Determine lists of various kinds and their subtypes
        self.BuildHierarchies()

        # Add kinds of roles
        # Add kinds of role_players to kinds of binary relations because of relation types
        for rel_type in self.rel_types:
            rel_type.role_players_types, rel_type.role_player_type_lh, \
                rel_type.role_player_type_rh = self.Determine_role_players_types(rel_type.uid)

    def Add_name_in_context(self, lang_uid, comm_uid, name, naming_uid, description):
        ''' Add a name_in_context and description to object.names_in_contexts
            and add the name_in_context to the dictionary.
            A name_in_context is a triple: language_uid, language_community_uid, name.
            A name_and_description
            is a name_in_context extended with a naming_uid and a description.
        '''
        name_and_descr = (lang_uid, comm_uid, name, naming_uid, description)
        name_in_context = (lang_uid, comm_uid, name)
        if name_and_descr not in obj.names_in_contexts:
            obj.names_in_contexts.append(name_and_descr)
        if name_in_context not in self.dictionary:
            value_triple = (obj.uid, naming_uid, description)
            self.dictionary[name_in_context] = value_triple

    def Add_row_to_network(self, row, names_and_descriptions):
        '''Add a row (that contains an expression) to the network.'''

        # Take the uids and names from row
        idea_uid = row[idea_uid_col]
        lang_uid = row[lang_uid_col]
        comm_uid = row[comm_uid_col]
        # intent_uid = row[intent_uid_col]
        lh_uid, lh_name = row[lh_uid_col], row[lh_name_col]
        rh_uid, rh_name = row[rh_uid_col], row[rh_name_col]
        rel_type_uid = row[rel_type_uid_col]
        # rel_type_name = row[rel_type_name_col]
        phrase_type_uid = row[phrase_type_uid_col]
        description = row[part_def_col]
        uom_uid, uom_name = row[uom_uid_col], row[uom_name_col]

        # If the left or right hand object name is blank then give it the name 'nameless'
        if lh_name == '':
            if lang_uid == Dutch_uid:
                lh_name = self.nameless[1]
            else:
                lh_name = self.nameless[0]

        if rh_name == '':
            if lang_uid == Dutch_uid:
                rh_name = self.nameless[1]
            else:
                rh_name = self.nameless[0]

        # Collect used languages for naming left hand objects in dict.
        # (for use by preferences)
        if lang_uid not in self.lang_uid_dict:
            self.lang_uid_dict[lang_uid] = row[lang_name_col]
            if lang_uid not in self.uid_dict:
                lang = Anything(lang_uid, row[lang_name_col])
                lang.defined = False
                self.objects.append(lang)
                self.uid_dict[lang_uid] = lang
            # Add language object to list of undefined_objects
            # for later verification of the presence of a definition
            self.undefined_objects.append(lang)

        # Collect language communities for naming left hand objects in dict.
        # (for use by preferences)
        if comm_uid not in self.community_dict:
            self.community_dict[comm_uid] = row[comm_name_col]
            if comm_uid not in self.uid_dict:
                comm = Anything(comm_uid, row[comm_name_col])
                comm.defined = False
                comm.candidate_names.append(row[comm_name_col])
                self.objects.append(comm)
                self.uid_dict[comm_uid] = comm
                # Add comm to list of undefined_objects
                # for later verification of the presence of a definition
                self.undefined_objects.append(comm)

        # Create the left hand object if it does not exist and add to naming_table dictionary
        if lh_uid not in self.uid_dict:
            # If left hand object name is 'nameless' then add the uid to the term,
            # thus creating the new name: nameless-uid
            if lh_name in self.nameless:  # ['nameless', 'naamloos', '']
                ind = 0
                if lang_uid == Dutch_uid:
                    ind = 1
                lh_name = self.nameless[ind] + '-' + str(lh_uid)

            # Determine the naming_uid for the name_in_context and description
            if rel_type_uid in self.alias_uids:
                naming_uid = rel_type_uid
            else:
                naming_uid = is_called_uid

            # Verify uniqueness of name_in_context and if unique, then add to dictionary
            lh_name_in_context = (lang_uid, comm_uid, lh_name)
            if lh_name_in_context in self.dictionary:
                # Check whether the same name in the same language and language community
                # has indeed the same uid (otherwise it should be a homonym
                # with different language and/or language community)
                verification_triple = self.dictionary[lh_name_in_context]
                if verification_triple[0] != lh_uid:
                    Message(self.GUI_lang_index,
                            'The same name <{}> in the same language and language community '
                            'shall have the same UIDs instead of {} and {}. Idea {} ignored.'.
                            format(lh_name_in_context[2], lh_uid,
                                   verification_triple[0], idea_uid),
                            'Dezelfde naam <{}> in dezelfde taal en taalgemeenschap moeten '
                            'dezelfde UIDs hebben, in plaats van {} en {}. Idee {} is genegeerd'.
                            format(lh_name_in_context[2], lh_uid,
                                   verification_triple[0], idea_uid))
                    return
            else:
                # Add name_in_context to dictionary of names in contexts
                value_triple = (lh_uid, naming_uid, description)
                self.dictionary[lh_name_in_context] = value_triple

            # Create new (lh) object
            lh = Anything(lh_uid, lh_name)
            self.objects.append(lh)
            self.uid_dict[lh_uid] = lh

            # Add name and description to object list of names_in_contexts with description
            lh_name_and_descr = (lang_uid, comm_uid, lh_name, naming_uid, description)
            if rel_type_uid in self.specialRelUIDs or rel_type_uid in self.classifUIDs:
                lh.defined = True
                lh.names_in_contexts.append(lh_name_and_descr)
            elif rel_type_uid in self.alias_uids:
                lh.names_in_contexts.append(lh_name_and_descr)

            # If names and descriptions in other languages are available add them as well
            if len(names_and_descriptions) > 0:
                for name_and_description in names_and_descriptions:
                    lh.names_in_contexts.append(name_and_description)

        else:
            # lh_uid is known, thus find the existing lh object from its uid in uid_dict.
            lh = self.uid_dict[lh_uid]

            # If existing lh.name is 'nameless-uid', but new lh_name is given,
            #    then insert name_and_descr and change the name from nameless into the given name
            ind = 0
            if lang_uid == Dutch_uid:
                ind = 1
            if lh.name == self.nameless[ind] + '-' + str(lh_uid) \
               and lh_name not in self.nameless:
                lh_name_and_descr = (lang_uid, comm_uid, lh_name, is_called_uid, description)
                lh.names_in_contexts.insert(0, lh_name_and_descr)
                lh.name = lh_name

            # If rel_type is an alias relation, then add name_in_context to object and to dict
            if rel_type_uid in self.alias_uids:
                if lh_name not in self.nameless \
                   and lh_name != self.nameless[ind] + '-' + str(lh_uid):
                    naming_uid = rel_type_uid
                    self.Add_name_in_context_to_obj_and_dict(
                        lh, lang_uid, comm_uid, lh_name, lh_uid, naming_uid, description)
                # If alias names and descriptions in other languages are available add them as well
                if len(names_and_descriptions) > 0:
                    for name_and_description in names_and_descriptions:
                        if name_and_description not in lh.names_in_contexts:
                            lh.names_in_contexts.append(name_and_description)
            # If rel_type is a subtyping relation then add name_in_context to object and to dict
            elif rel_type_uid in self.specialRelUIDs or rel_type_uid in self.classifUIDs:
                if lh_name not in self.nameless \
                   and lh_name != self.nameless[ind] + '-' + str(lh_uid):
                    naming_uid = is_called_uid
                    lh.defined = True
                    self.Add_name_in_context_to_obj_and_dict(
                        lh, lang_uid, comm_uid, lh_name, lh_uid, naming_uid, description)
                # If names and descriptions in other languages are available add them as well
                if len(names_and_descriptions) > 0:
                    for name_and_description in names_and_descriptions:
                        lh.names_in_contexts.append(name_and_description)

        # If rh object does not exist yet, then create an object with a name
        # and with a temporary name for later verification,
        # but without a name_in_context and without a description and defined = False
        if rh_uid not in self.uid_dict:
            #  Create new (rh) object
            rh = Anything(rh_uid, rh_name)
            rh.defined = False
            rh.candidate_names.append(rh_name)
            self.objects.append(rh)
            self.uid_dict[rh_uid] = rh
            # Add rh to list of undefined_objects
            # for later verification of the presence of a definition
            self.undefined_objects.append(rh)

        # rh object is known
        else:
            # Find rh object in the uid dictionary
            rh = self.uid_dict[rh_uid]
            # Verify whether rh_name is included in rh.names_in_contexts
            # If rh_name is still unknown, then collect the rh_names in candidate_names
            # for future reference (and add rh to list of potentially undefined_objects
            existing_name = False
            for name_in_context in rh.names_in_contexts:
                if rh_name == name_in_context[2]:
                    existing_name = True
            if existing_name is False:
                if rh_name not in rh.candidate_names:
                    rh.candidate_names.append(rh_name)
                    self.undefined_objects.append(rh)

        # UOM
        # Verify existence of a unit of measure in this expression
        if uom_uid != '' and uom_uid != '0':
            if uom_uid not in self.uid_dict:
                Message(self.GUI_lang_index,
                        'The unit of measure {} ({}) is used before being defined.'.
                        format(uom_name, uom_uid),
                        'De meeteenheid {} ({}) is gebruikt voordat hij is gedefinieerd.'.
                        format(uom_name, uom_uid))
                uom = Anything(uom_uid, uom_name)
                uom.defined = False
                uom.candidate_names.append(uom_name)
                self.objects.append(uom)
                self.uid_dict[uom_uid] = uom
                # Add uom to list of undefined_objects
                # for later verification of the presence of a definition
                self.undefined_objects.append(uom)
            else:
                # Find uom in the uid dictionary
                uom = self.uid_dict[uom_uid]
        else:
            # Equality of 'none' object (with uid == '')
            uom = self.non_object

        # Rel
        # Create a relation object (with uid = idea_uid)
        # and add the relation between objects to both objects, except when lh == rh
        if rh_uid != lh_uid:
            rel_type = self.uid_dict[rel_type_uid]

            # If base_ontology is created, then kinds of relations have kinds of roles
            if self.base_ontology is True:
                # If no lh or rh kinds of roles are given then allocate kind of role
                # conform first and second role of kind of relation
                if row[lh_role_uid_col] == '':
                    if phrase_type_uid == basePhraseUID:
                        row[lh_role_uid_col] = rel_type.first_role.uid
                        row[lh_role_name_col] = rel_type.first_role.name
                    else:
                        row[lh_role_uid_col] = rel_type.second_role.uid
                        row[lh_role_name_col] = rel_type.second_role.name
                if row[rh_role_uid_col] == '':
                    if phrase_type_uid == basePhraseUID:
                        row[rh_role_uid_col] = rel_type.second_role.uid
                        row[rh_role_name_col] = rel_type.second_role.name
                    else:
                        row[rh_role_uid_col] = rel_type.first_role.uid
                        row[rh_role_name_col] = rel_type.first_role.name

            # Default: category == None
            relation = Relation(lh, rel_type, rh, phrase_type_uid, uom, row)

            # Add the relation between related objects
            # (self.obj_1 and self.obj_2) and the self.rel_type object to both objects
            lh.add_relation(relation)
            rh.add_relation(relation)

            self.idea_uids.append(idea_uid)
            self.rels.append(relation)

            # Add information to object depending in kind of relation (rel_type_uid)
            # If rel_type is a specialization relation (1146 or one of its subtypes),
            # then add subtype and supertype to lh and rh object
            if rel_type_uid in self.specialRelUIDs:
                if phrase_type_uid == basePhraseUID:
                    lh.name = lh_name
                    lh.add_supertype(rh)
                    lh.kind = lh.supertypes[0]
                    rh.add_subtype(lh)
                    # Set lh object category as 'kind' after check
                    # on consistency with earlier categorization
                    if lh.category != 'anything' and lh.category not in self.categories_of_kinds:
                        Message(self.GUI_lang_index,
                                "Warning: Idea {}: Object '{}' category '{}' is inconsistent "
                                "with earlier categorization as 'kind'.".
                                format(idea_uid, lh_name, lh.category),
                                "Warning: Idea {}: Object '{}' category '{}' is inconsistent "
                                "with earlier categorization as 'kind'.".
                                format(idea_uid, lh_name, lh.category))
                    else:
                        # lh category is not yet categorized
                        # (initially by default set as 'anything')
                        if rh.category == 'anything':
                            lh.category = 'kind'
                            rh.category = 'kind'
                        else:
                            lh.category = rh.category
                # For the inverse
                else:
                    lh.add_subtype(rh)
                    rh.add_supertype(lh)

            # If classification relation (1225 or one of its subtypes),
            # then add classifier and classified to objects
            elif rel_type_uid in self.classifUIDs:
                if phrase_type_uid == basePhraseUID:
                    lh.name = lh_name
                    lh.add_classifier(rh)
                    rh.add_individual(lh)
                    lh.kind = lh.classifiers[0]
                    # Set object category as 'individual' after check
                    # on consistency with earlier classification
                    if lh.category != 'anything':
                        if lh.category not in ['individual', 'physical object',
                                               'aspect', 'occurrence', 'role']:
                            Message(self.GUI_lang_index,
                                    "Error: Idea {}: Object '{}' category '{}' should "
                                    "be 'individual object'".
                                    format(idea_uid, lh_name, lh.category),
                                    "Fout: Idee {}: Object '{}' categorie '{}' zou "
                                    "'individueel object' moeten zijn".
                                    format(idea_uid, lh_name, lh.category))
                            lh.category = 'individual'
                    else:
                        # lh object category is still the default ('anything')
                        # thus make it 'individual'
                        # rh object category should be 'kind' or one of its subtypes
                        lh.category = 'individual'
                        if rh.category == 'anything':
                            rh.category = 'kind'
                        elif rh.category not in ['kind', 'kind of physical object',
                                                 'kind of aspect', 'kind of occurrence',
                                                 'kind of role', 'kind of relation',
                                                 'number']:
                            Message(self.GUI_lang_index,
                                    "Error: Idea {}: Object '{}' category '{}' should be 'kind'".
                                    format(idea_uid, rh_name, rh.category),
                                    "Fout: Idee {}: Object '{}' categorie '{}' zou 'soort' moeten "
                                    "zijn".
                                    format(idea_uid, rh_name, rh.category))
                            rh.category = 'kind'
                else:
                    lh.add_individual(rh)
                    rh.add_classifier(lh)
            # If part-whole relation (composUID 1260 or concComposUID 1261
            # or one of their subtypes),
            # then add part to collection of parts of the whole object
            elif rel_type_uid in self.subComposUIDs or \
                    rel_type_uid in self.subConcComposUIDs:
                if phrase_type_uid == basePhraseUID:
                    rh.add_part(lh)
                else:
                    lh.add_part(rh)

            # If rel_type_uid == uid of <has by definition as first/second role a> relation
            # then add first/second kind of role to the kind of relation
            elif rel_type_uid == first_role_uid:
                if phrase_type_uid == basePhraseUID:
                    lh.add_first_role(rh)
            elif rel_type_uid == second_role_uid:
                if phrase_type_uid == basePhraseUID:
                    lh.add_second_role(rh)

            # If rel_type_uid == uid of <is by definition a role of a> kind of role player,
            # then add the kind of role_player to the kind of role
            elif rel_type_uid == by_def_role_of_ind:
                lh.add_role_player(rh)
                if phrase_type_uid == basePhraseUID:
                    # Verify whether lh is indeed a kind of role
                    if lh.category == 'anything':
                        lh.category = 'kind of role'
                    elif lh.category != 'kind of role':
                        Message(self.GUI_lang_index,
                                "** Warning: Idea {} object ({}) {} expects being "
                                "a kind of role and not a {}".
                                format(idea_uid, lh.uid, lh.name, lh.category),
                                "** Waarschuwing: Idee {}: object ({}) {} wordt verwacht "
                                "een soort rol te zijn en niet een {}".
                                format(idea_uid, lh.uid, lh.name, lh.category))
        else:
            # lh_uid == rh_uid
            # If rel_type_uid == uid of <is a base phrase for> (6066) name of a kind of relation
            # or rel_type_uid == uid of <is a inverse phrase for> (1986)name of a kind of relation,
            # then add the name in context to the list of base phrases
            #      resp. inverse phrase in context
            # for the object and add the name to the list of base_phrases or inverse_phrases
            # Including phrases for possible other languages
            if rel_type_uid == basePhraseUID:
                phrase_in_context = [lang_uid, comm_uid, lh_name]
                lh.add_base_phrase(phrase_in_context)
                lh.base_phrases.append(lh_name)
                self.total_base_phrases.append(lh_name)
                # If base phrases (and descriptions) in other languages are available
                # then add them as well
                if len(names_and_descriptions) > 0:
                    for name_and_description in names_and_descriptions:
                        lh.add_base_phrase(name_and_description)
                        lh.base_phrases.append(name_and_description[2])
                        self.total_base_phrases.append(name_and_description[2])
            elif rel_type_uid == inversePhraseUID:
                phrase_in_context = [lang_uid, comm_uid, lh_name]
                lh.add_inverse_phrase(phrase_in_context)
                lh.inverse_phrases.append(lh_name)
                self.total_inverse_phrases.append(lh_name)
                # If inverse phrases and descriptions in other languages are available
                # then add them as well
                if len(names_and_descriptions) > 0:
                    for name_and_description in names_and_descriptions:
                        lh.add_inverse_phrase(name_and_description)
                        lh.inverse_phrases.append(name_and_description[2])
                        self.total_inverse_phrases.append(name_and_description[2])

    def Add_name_in_context_to_obj_and_dict(self, lh, lang_uid, comm_uid,
                                            lh_name, lh_uid, naming_uid, description):
        ''' Create tuples for name_in_context and name_in_context_plus_description
            and add them to dictionary and to object resp.
        '''
        lh_name_and_descr = (lang_uid, comm_uid, lh_name, naming_uid, description)
        if lh_name_and_descr not in lh.names_in_contexts:
            lh.names_in_contexts.append(lh_name_and_descr)
        lh_name_in_context = (lang_uid, comm_uid, lh_name)
        if lh_name_in_context not in self.dictionary:
            value_triple = (lh_uid, naming_uid, description)
            self.dictionary[lh_name_in_context] = value_triple

    def BuildHierarchies(self):
        ''' Build lists of subtype concepts and subtype concept_uids of various kinds,
            including the kinds themselves.
        '''
        # Determine lists of various kinds and their subtypes
        self.sub_classifs, self.sub_classif_uids = self.Determine_subtype_list(classifUID)
        self.subClassifieds, self.subClassifiedUIDs = self.Determine_subtype_list(classifiedUID)
        self.indOrMixRels, self.indOrMixRelUIDs = self.Determine_subtype_list(indOrMixRelUID)
        # indivRelUID = 4658 binary relation between individual things
        self.indivBinRels, self.indivBinRelUIDs = self.Determine_subtype_list(indivRelUID)
        self.kindHierRels, self.kindHierRelUIDs = self.Determine_subtype_list(kindHierUID)
        self.kindKindRels, self.kindKindRelUIDs = self.Determine_subtype_list(kindKindUID)
        self.kindBinRels, self.kindBinRelUIDs = self.Determine_subtype_list(kindRelUID)
        self.mixedBinRels, self.mixedBinRelUIDs = self.Determine_subtype_list(mixedRelUID)
        self.specialRels, self.specialRelUIDs = self.Determine_subtype_list(specialRelUID)
        # subtypeRoleUID = 3818 UID of 'subtype' (role)
        self.subtypeSubs, self.subtypeSubUIDs = self.Determine_subtype_list(subtypeRoleUID)
        self.subPossAsps, self.subPossAspUIDs = self.Determine_subtype_list(possAspUID)
        self.subPossessors, self.subPossessorUIDs = self.Determine_subtype_list(possessorUID)
        self.transitiveRel, self.transitiveRelUIDs = self.Determine_subtype_list(transRelUID)
        # concPossAspUID = 2069
        self.subConcPossAsps, self.subConcPossAspUIDs = self.Determine_subtype_list(concPossAspUID)
        # concComplRelUID = 4902
        self.subConcComplRels, self.subConcComplRelUIDs = \
            self.Determine_subtype_list(concComplRelUID)
        # qualSubtypeUID = 4328
        self.qualSubtypes, self.qualSubtypeUIDs = self.Determine_subtype_list(qualSubtypeUID)
        # qualOptionsUID = 4848
        self.qualOptionss, self.qualOptionsUIDs = self.Determine_subtype_list(qualOptionsUID)
        self.concCompls, self.concComplUIDs = self.Determine_subtype_list(concComplUID)   # 4951
        self.concQuants, self.concQuantUIDs = self.Determine_subtype_list(concQuantUID)   # 1791
        self.subQuals, self.subQualUIDs = self.Determine_subtype_list(qualifUID)
        # quantUID = 2044 quantification
        self.subQuants, self.subQuantUIDs = self.Determine_subtype_list(quantUID)
        self.subInformatives, self.subInformativeUIDs = self.Determine_subtype_list(informativeUID)
        self.subOccurrences, self.subOccurrenceUIDs = self.Determine_subtype_list(occurrenceUID)
        # composUID = composition relation and its subtypes
        self.subComposs, self.subComposUIDs = self.Determine_subtype_list(composUID)
        # componUID = component role and its subtypes
        self.subCompons, self.subComponUIDs = self.Determine_subtype_list(componUID)
        # concComposUID = conceptual composition relation and its subtypes
        self.subConcComposs, self.subConcComposUIDs = self.Determine_subtype_list(concComposUID)
        # concComponUID = conceptual component role and its subtypes
        self.subConcCompons, self.subConcComponUIDs = self.Determine_subtype_list(concComponUID)
        # 4546 = being a second role in an <involvement in an occurrence> relation
        # self.subInvolveds, self.subInvolvedUIDs = self.Determine_subtype_list(involvedUID)
        # involvUID = 4767 = involvement in an occurrence (relation)
        self.subInvolvs, self.subInvolvUIDs = self.Determine_subtype_list(involvUID)
        # nextUID = 5333 next element (role)
        self.subNexts, self.subNextUIDs = self.Determine_subtype_list(nextUID)
        self.subtypesOfShall, self.subtypesOfShall = self.Determine_subtype_list(shallUID)
        self.aliass, self.alias_uids = self.Determine_subtype_list(aliasUID)
        self.concWholes, self.concWholeUIDs = self.Determine_subtype_list(concWholeUID)
        self.concPosss, self.concPossUIDs = self.Determine_subtype_list(concPosessorUID)
        self.transs, self.transUIDs = self.Determine_subtype_list(transUID)
        # classifUID = 1225 classification relation
        self.classifs, self.classifUIDs = self.Determine_subtype_list(classifUID)
        self.specials, self.specialUIDs = self.Determine_subtype_list(specialUID)
        # concBinRelKindsUID = 1231 = conc.bin. relation between things of specified kinds.
        self.concBinRelbetKinds, self.concBinRelbetKinds = \
            self.Determine_subtype_list(concBinRelKindsUID)
        # self.props, self.propUIDs = self.Determine_subtype_list(propUID)  # 551004 = property
        # 4714 = can be a role of a
        self.conc_playings, self.conc_playing_uids = self.Determine_subtypes_of_kind('4714')

    def Determine_subtypes_of_kind(self, kind_uid):
        ''' Determine the list of a kind and its subtypes and the list of their uids.'''
        kind = self.uid_dict[kind_uid]
        all_subs = []
        all_sub_uids = []
        if kind is None:
            Message(self.GUI_lang_index,
                    'The kind {} is not found.'.format(kind_uid),
                    'De soort {} is niet gevonden.'.format(kind_uid))
        else:
            direct_subs = kind.subtypes
            if len(direct_subs) > 0:
                # Add the direct subtypes to all_subs (if not yet present)
                for sub in direct_subs:
                    if sub not in all_subs:
                        all_subs.append(sub)
                        all_sub_uids.append(sub.uid)
                for sub_i in all_subs:
                    sub_subs = sub_i.subtypes
                    if len(sub_subs) > 0:
                        # Extent the all_subs with sub-subtypes (if not yet present)
                        for sub_sub in sub_subs:
                            if sub_sub not in all_subs:
                                all_subs.append(sub_sub)
                                all_sub_uids.append(sub_sub.uid)

            # Finally insert kind and uid as the first ones in the list
            all_subs.insert(0, kind)
            all_sub_uids.insert(0, kind.uid)
        return all_subs, all_sub_uids

    def Determine_subtype_list(self, kind_uid):
        ''' Determine the list of a kind and its subtypes and the list of their uids'''
        kind = self.uid_dict[kind_uid]
        if kind is None:
            Message(self.GUI_lang_index,
                    'The kind {} is not found.'.format(kind_uid),
                    'De soort {} is niet gevonden.'.format(kind_uid))
        sub_kinds, sub_kind_uids = self.Determine_subtypes(kind)
        sub_kinds.insert(0, kind)
        sub_kind_uids.insert(0, kind_uid)
        return sub_kinds, sub_kind_uids

    def Determine_subtypes(self, supertype):
        '''Determine and return all_subtype_objects and all_subtype_uids of supertype
           (except the supertype itself) including subSubs etc. and
           if supertype.uid = binRelUID (5935, binary relation),
           then start building the relRolesTable
        '''
        # Collect subtypes of a given supertypeUID. E.g. binary relation (5935)
        all_subtype_objects = []
        all_subtype_uids = []
        top = supertype
        rel_taxonomy = False
        # if supertypeUID == binary relation (5935)
        if top.uid == binRelUID:
            rel_taxonomy = True

        # Collect the subtypes of the supertype in focus
        subs = supertype.subtypes
        if len(subs) > 0:
            for sub in subs:
                # Add each subtype to the list of subtypes
                if sub not in all_subtype_objects:
                    # Add subtype to total list of subtypes
                    all_subtype_objects.append(sub)
                    all_subtype_uids.append(sub.uid)

                    # If sub belongs to taxonomy of relations then
                    # inherit by definition the first and second kinds of roles
                    if rel_taxonomy is True:
                        self.Inherit_kinds_of_roles(sub, supertype)
                # Debug print ('Supertype:',supertype.uid,"Subtypes:",subs,subtypeRow)

            # For each subtype determine the further subtypes
            for subX in subs:
                # List of subtypes if possibly empty! Then the loop terminates
                sub_subs = subX.subtypes
                for sub in sub_subs:
                    # Add the sub_sub to the list of subtypes
                    if sub not in all_subtype_objects:
                        all_subtype_objects.append(sub)
                        all_subtype_uids.append(sub.uid)
                        # Increase the list of subs that is current
                        subs.append(sub)

                        # If sub belongs to taxonomy of relations
                        # then inherit by definition first and second kinds of roles
                        if rel_taxonomy is True:
                            self.Inherit_kinds_of_roles(sub, subX)
        return all_subtype_objects, all_subtype_uids

    def Inherit_kinds_of_roles(self, rel, supertype):
        ''' If rel (a kind of relation) has no defined (first or second) kind of role, then
            allocate the kind of role of the supertype to the subtype kind of relation.
            If the kind of relation has a defined kind of role, then
            verify whether that kind of role has one or more supertypes and if yes, then
            verify whether one of those supertypes
            is equal to the kind of role of the supertype of the kind of relation.
        '''
        rel.category = 'kind of relation'
        try:
            if rel.first_role:  # != None:
                # Check whether the supertype of the kind of role == the role
                # of the supertype of the kind of relation
                # equality = False
                if len(rel.first_role.supertypes) > 0:
                    for supertype_role in rel.first_role.supertypes:
                        if supertype_role == supertype.first_role:
                            # equality = True
                            break
                else:
                    Message(self.GUI_lang_index,
                            'The first kind of role <{}> has no supertypes'.
                            format(rel.first_role.name),
                            'De eerste soort rol <{}> heeft geen supertypes'.
                            format(rel.first_role.name))
                # Debug print('rel.first_role_def:', rel.first_role.name)
            # else:
                # Debug print('rel.first_role_inh:', rel.first_role.name)
        except AttributeError:
            rel.first_role = supertype.first_role
            # Debug print('rel.inherited first_role', rel.name, rel.uid, rel.first_role.name)

        try:
            if rel.second_role is not None:
                # Check whether the supertype of the kind of role == the role
                # of the supertype of the kind of relation
                # equality = False
                if len(rel.second_role.supertypes) > 0:
                    for supertype_role in rel.second_role.supertypes:
                        if supertype_role == supertype.second_role:
                            # equality = True
                            break
                else:
                    Message(self.GUI_lang_index,
                            'The second kind of role <{}> has no supertypes'.
                            format(rel.second_role.name),
                            'De tweede soort rol <{}> heeft geen supertypes'.
                            format(rel.second_role.name))
        except AttributeError:
            rel.second_role = supertype.second_role

    def Determine_role_players_types(self, rel_uid):
        ''' Individual or kind? Determine whether the query relation type denotes:
                                (1) a relation between individual things
                             or (2) between kinds
                             or (3) between an individual and a kind
                             or (4) between an individual and either another individual
                                    or a kind (a combination of (1) and (3))
        '''
        rolePlayersTypes = 'unknown'
        rolePlayerTypeLH = 'unknown'    # Required kind of LH object, because of kind of rel_uid
        rolePlayerTypeRH = 'unknown'    # Required kind of RH object
        int_rel_uid, integer = Convert_numeric_to_integer(rel_uid)

        # Determine the category of lh and rh role players on the basis of the kind of relation
        if int_rel_uid >= 100:
            # If rel_uid is a subtype of 4658 = binary relation between individual things
            if rel_uid in self.indivBinRelUIDs:
                rolePlayersTypes = 'individuals'
                rolePlayerTypeLH = 'individual'
                rolePlayerTypeRH = 'individual'

            # If rel_uid is a subtype of 5052 = hierarchical relation between kinds of things
            elif rel_uid in self.kindHierRelUIDs:
                rolePlayersTypes = 'hierOfKinds'
                rolePlayerTypeLH = 'kind'
                rolePlayerTypeRH = 'kind'

            # If rel_uid is a subtype of 1231 = binary relation between things of specified kinds
            elif rel_uid in self.kindKindRelUIDs:
                rolePlayersTypes = 'thingsOfKinds'
                rolePlayerTypeLH = 'kind'
                rolePlayerTypeRH = 'kind'

            # kindBinRelUIDs: subtypes of 5937 = binary relation between kinds of things
            # elif rel_uid in self.kindBinRelUIDs:
            #    rolePlayersTypes = 'kinds'

            # If rel_uid is a subtype of 6068 = binary relation between an individual thing and any
            # (kind or individual)
            elif rel_uid == indOrMixRelUID:
                rolePlayersTypes = 'individualsOrMixed'  # is related to (a)
                # Debug print('RolePlayers-IndividualsOrMixed:',
                #              rolePlayersTypes, relName, self.total_base_phrases)

            # If rel_uid is a subtype of binary relation between an individual thing and a kind
            elif rel_uid in self.mixedBinRelUIDs:
                rolePlayersTypes = 'mixed'

            # If rel_uid is a subtype of 7071 = binary relation
            # between a kind and any (kind or individual)
            elif rel_uid == kindAndMixRelUID:
                rolePlayersTypes = 'kindsOrMixed'  # can be related to (a)
            else:
                rolePlayersTypes = 'other'
        else:
            Message(self.GUI_lang_index,
                    'The uid {} of a kind of relation is unknown.'.format(rel_uid),
                    'De uid {} van een soort relatie is onbekend.'.format(rel_uid))
        return rolePlayersTypes, rolePlayerTypeLH, rolePlayerTypeRH

    def Verify_network(self):
        ''' Execute various checks on completeness
            and consistency of the semantic network.
        '''
        # Check whether each concept has at least
        # one supertype concept or at least one classifier.
        for obj in self.objects:
            if obj.category in ['kind', 'kind of physical object',
                                'kind of occurrence', 'kind of aspect',
                                'kind of role', 'kind of relation']:
                if len(obj.supertypes) == 0 and obj.uid != '730000':
                    Message(self.GUI_lang_index,
                            'Kind ({}) {} has no supertype(s).'.format(obj.uid, obj.name),
                            'Soort ({}) {} heeft geen supertype(s).'.format(obj.uid, obj.name))
            elif obj.category in ['individual', 'physical object', 'occurrence', 'aspect',
                                  'role', 'relation']:
                if len(obj.classifiers) == 0:
                    Message(self.GUI_lang_index,
                            'Individual object ({}) {} has no classifier(s).'.
                            format(obj.uid, obj.name),
                            'Individueel object ({}) {} heeft geen classificeerder(s).'.
                            format(obj.uid, obj.name))
            elif obj.category not in ['number', 'anything']:
                Message(self.GUI_lang_index,
                        'The category of object {} ({}) is {}, which is unexpected.'.
                        format(obj.name, obj.uid, obj.category),
                        'De categorie van object {} ({}) is {}, hetgeen onverwacht is.'.
                        format(obj.name, obj.uid, obj.category))

    def Query_network_dict(self, search_string, string_commonality):
        '''Search for string as (part of) name in a names_in_contexts dictionary.
           The string_commonality specifies to what extent the string
           should correspond with the name.
           A list of candidates is returned.
           E.g.: term_in_context, value_triple =
                 {('910036', '193259', "anything"), ('730000', '5117', 'descr'))
        '''
        # Split search_string in 'chunks' separated by one or more spaces
        # while treating multiple consecutive whitespaces as one separator
        chunks = search_string.split(None)
        ref_list = []
        candids = []
        first_chunk = False
        for chunk in chunks:
            if first_chunk is False:
                # Find list of candidates based on first chunk. Use that list as a reference list
                cand_list = list(self.dictionary.filter_on_key(chunk, string_commonality))
                ref_list = cand_list[:]
                first_chunk = True
            elif len(chunks) > 1:
                candids[:] = []
                string_commonality = 'cspi'
                chunk_list = list(self.dictionary.filter_on_key(chunk, string_commonality))
                if len(chunk_list) > 0:
                    for chunk_candid in chunk_list:
                        # Check whether chunck_candid also appears in first list of candidates
                        if chunk_candid in ref_list:
                            candids.append(chunk_candid)
                    ref_list = candids[:]
                # Debug print('Chunks:', ref_list)

        # candidates = list(cand_dict)
        # Debug print('Nr of candidates for {} is {}'.format(search_string, len(candidates)))
        return ref_list

    def Find_object_by_name(self, name, string_commonality):
        '''Search for object uid by name in semantic network.
           Present candidates to user and select candidate or confirm single candidate.
           Floating point numbers should be a notation with decimal dots,
           for example in 1234.567 notation or its equivalent value 1,234.567.
           Semicolons (;) optionally followed by one or more spaces separates values.
           For example 3D coordinates may be given as: 1.0; 2.3; 3.4
        '''
        # Debug print("  Search for object with name '%s'." % (name))
        uid_unknown = False
        candid_nr = 0
        self.uid_name_desc_list[:] = []

        # Determine the uid for an integer when the name is a positive or negative whole number.
        int_uid = self.Determine_uid_for_integer(name)
        # int_uid > 0 means integer number is found
        #                   and allocated uid is in range 2.000.000.001-2.999.999.999
        # Non whole numbers should be found in the dictionary (for the time being)
        if int_uid > 0:
            candidates = []
            international = '589211'  # language
            community = '191697'  # language community mathematics
            term_in_context = [international, community, name]
            value_triple = [str(int_uid), is_called_uid, 'decimal number ' + name]
            candidates.append([term_in_context, value_triple])
            # Debug print('Whole number', candidates[0])
        else:
            # Search for list of candidates: [term_in_context, value_triple]
            candidates = self.Query_network_dict(name, string_commonality)

        if len(candidates) > 0:
            for candidate in candidates:
                candid_nr += 1
                # The uid is the first value in the value_triple
                obj_uid = candidate[1][0]
                # if len(candidates) > 1:
                #     Candidate[0] is lang_uid, comm_uid, obj_name of first candidate
                #     comm_name = self.comm_dict_NL[candidate[0][1]]
                #     Debug print("    Candidate {}: object {}, {} ({})".
                #          format(candid_nr, candidate[0][2], comm_name, obj_uid))
                # UID_name_desc is list [uid, name, description]
                uid_name_desc = [obj_uid, candidate[0][2], candidate[1][2]]
                self.uid_name_desc_list.append(uid_name_desc)
        else:
            # No candidates available, thus name is unknown.
            # Then collect unknown names and allocate UIDs in dictionary of new_things.
            uid_unknown = True
            if name not in self.new_things:
                self.new_obj_uid += 1
                if self.new_obj_uid < self.current_file.upper_obj_range_uid:
                    self.new_things[name] = self.current_file.prefix + str(self.new_obj_uid)
                    unknown_uid = str(self.new_obj_uid)
                else:
                    Message(self.GUI_lang_index,
                            'The upper limit for the range of UIDs {} is reached. '
                            'The unknown object {} is ignored.'.
                            format(self.current_file.upper_obj_range_uid, name),
                            'De bovengrens van de range van UIDs {} is bereikt. '
                            'Het onbekende object {} is genegeerd.'.
                            format(self.current_file.upper_obj_range_uid, name))
                    unknown_uid = '0'
            else:
                unknown_uid = self.new_things[name]
            candid_nr += 1
            Message(self.GUI_lang_index,
                    "No candidates for mapping found. Unknown {}: object ({}) {}".
                    format(candid_nr, unknown_uid, name),
                    "Geen kandidaten voor de mapping gevonden. Onbekende {}: object ({}) {}".
                    format(candid_nr, unknown_uid, name))
            uid_name_desc = [unknown_uid, name, '']
            self.uid_name_desc_list.append(uid_name_desc)

        # Select one of the candidates.
        selected = False
        while selected is False:
            # If two candidates with identical UIDs then select the first one
            if len(candidates) == 2 \
               and self.uid_name_desc_list[0][0] == self.uid_name_desc_list[1][0]:
                selected_uid_name_desc = self.uid_name_desc_list[0]
                selected = True
            elif len(candidates) > 1:
                if selected is False:
                    # If candidate selected earlier, then make the same selection
                    for uid_name_desc in self.uid_name_desc_list:
                        # Debug print('Compare {} with {}'.format(uid_name_desc[0],
                        #                                        self.select_dict))
                        if uid_name_desc[0] in self.select_dict:
                            selected_uid_name_desc = uid_name_desc
                            selected = True
                            continue
                    cand_str = input("Select candidate number "
                                     "or 'Enter' to select the first one: ")
                    if cand_str != '':
                        cand_nr = int(cand_str)
                        if cand_nr > 0 and cand_nr <= len(candidates):
                            selected_uid_name_desc = self.uid_name_desc_list[cand_nr - 1]
                            selected = True
                            self.select_dict[selected_uid_name_desc[0]] = selected_uid_name_desc
                        else:
                            Message(self.GUI_lang_index,
                                    "Incorrect entry '" + cand_nr + "'. Select again.",
                                    "Foutieve input '" + cand_nr + "'. Selecteer nogmaals.")
                    else:
                        # Selection = '', thus select the first candidate
                        selected_uid_name_desc = self.uid_name_desc_list[0]
                        selected = True
            else:
                # If 0 or 1 candidate then automatically select the single candidate or the unknown.
                selected_uid_name_desc = self.uid_name_desc_list[0]
                selected = True
        return uid_unknown, selected_uid_name_desc

    def Determine_uid_for_integer(self, string):
        ''' Determine a UID for a string that represents an integer number.
            First remove comma separation if present, e.g. -1,234 becomes -1234.
            Then verify whether the string value is a positive or negative integer number.
            Determine the uid: uid = 2.000.000.000 + pos_number or 1.000.000.000 - neg_number
        '''
        uid = 0
        commas_removed = string.replace(',', '')
        # Check on negative number
        if commas_removed[0] == '-':
            pos_number = - commas_removed
        else:
            pos_number = commas_removed
        if pos_number.isdecimal():
            number = int(pos_number)
            if commas_removed[0] == '-':
                uid = 1000000000 + number
            else:
                uid = 2000000000 + number
        return uid

    def save_pickle_db(self, widget):
        ''' Save the semantic network by a pickle dump.'''
        semantic_net = open(self.semantic_file_name, "bw")
        pickle.dump(self, semantic_net)
        semantic_net.close()
        Message(self.GUI_lang_index,
                "Network '{}' is saved in file {}.".
                format(self.name, self.semantic_file_name),
                "Netwerk '{}' is opgeslagen in file {}.".
                format(self.name, self.semantic_file_name))


if __name__ == "__main__":
    # Create and initialize a semantic network
    net_name = 'Semantic network'
    network = Semantic_Network(net_name)

    # Choose GUI language and formal language
    formal_language = "English"

    # Create a naming dictionary
    dict_name = 'Gellish Multilingual Taxonomic Dictionary'
    Gel_dict = GellishDict(dict_name)
    print('Created dictionary:', Gel_dict.name)

    # Build semantic network
    # ===to be done===

    network.save_pickle_db()

    # Query things in network
    qtext = input("\nEnter query string: ")
    while qtext != "quit" and qtext != "exit":
        # (cipi, cspi, cii, csi, cifi, csfi)
        com = input("\nEnter string commonality (cspi, csi): ")
        # string_commonality 'csi' = 'case sensitive identical'
        #                    'cspi' = 'case sensitive partially identical'
        string_commonality = 'cspi'
        candidates = network.Query_network_dict(qtext, string_commonality)
        if len(candidates) > 0:
            for candidate in candidates:
                obj_uid = candidate[1][0]
                # Debug print("candidate %s %s" % (obj_uid, candidate[0][2]))
                obj = network.uid_dict[obj_uid]     # find_object(obj_uid)
                s = obj.show(network)
        else:
            print("No candidates found")
        qtext = input("\nEnter query string: ")
