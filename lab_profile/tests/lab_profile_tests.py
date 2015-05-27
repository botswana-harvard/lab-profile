from django.test import TestCase

from edc.core.bhp_variables.models import StudySite
from edc.entry_meta_data.models import RequisitionMetaData
# from edc.lab.lab_clinic_api.models import Aliquot
from edc.lab.lab_profile.classes import site_lab_profiles
from edc.lab.lab_profile.exceptions import AlreadyRegistered as AlreadyRegisteredLabProfile
from edc.subject.appointment.models import Appointment
from edc.subject.lab_tracker.classes import site_lab_tracker
from edc.subject.registration.models import RegisteredSubject
from edc.subject.registration.tests.factories import RegisteredSubjectFactory
from edc.subject.visit_schedule.models import VisitDefinition
from edc.testing.classes import TestAppConfiguration
from edc.testing.classes import TestLabProfile
from edc.testing.classes import TestVisitSchedule
from edc.testing.models import TestPanel, TestAliquotType, TestReceive, TestAliquot
from edc.testing.tests.factories import TestConsentWithMixinFactory, TestRequisitionFactory


class LabProfileTests(TestCase):

    def setUp(self):
        from edc.testing.tests.factories import TestVisitFactory
        self.test_visit_factory = TestVisitFactory
        site_lab_tracker.autodiscover()
        try:
            site_lab_profiles.register(TestLabProfile)
        except AlreadyRegisteredLabProfile:
            pass
        TestAppConfiguration().prepare()
        site_lab_tracker.autodiscover()
        TestVisitSchedule().build()
        self.visit_definition = VisitDefinition.objects.get(code='1000')
        registered_subject = RegisteredSubjectFactory()
        self.test_consent = TestConsentWithMixinFactory(
            registered_subject=registered_subject, gender='M')
        self.registered_subject = RegisteredSubject.objects.get(
            subject_identifier=self.test_consent.subject_identifier)
        self.appointment = Appointment.objects.filter(
            registered_subject=self.registered_subject).order_by('visit_definition__time_point')[0]
        self.site = StudySite.objects.all()[0]

    def test_receives1(self):
        """assert received if drawn."""
        self.test_visit = self.test_visit_factory(appointment=self.appointment)
        requisition_panel = RequisitionMetaData.objects.filter(
            registered_subject=self.registered_subject)[0].lab_entry.requisition_panel
        panel = TestPanel.objects.get(name=requisition_panel.name)
        aliquot_type = TestAliquotType.objects.get(alpha_code=requisition_panel.aliquot_type_alpha_code)
        test_requisition = TestRequisitionFactory(
            test_visit=self.test_visit, site=self.site, panel=panel, aliquot_type=aliquot_type, is_drawn='Yes')
        lab_profile = site_lab_profiles.get(test_requisition._meta.object_name)
        self.assertIsInstance(lab_profile().receive(test_requisition), TestReceive)
        self.assertEqual(TestReceive.objects.get(
            requisition_identifier=test_requisition.requisition_identifier
            ).requisition_identifier, test_requisition.requisition_identifier)
        receive = TestReceive.objects.get(requisition_identifier=test_requisition.requisition_identifier)
        self.assertEqual(TestAliquot.objects.get(receive=receive).receive, receive)

    def test_receives2(self):
        self.test_visit = self.test_visit_factory(appointment=self.appointment)
        requisition_panel = RequisitionMetaData.objects.filter(
            registered_subject=self.registered_subject)[0].lab_entry.requisition_panel
        panel = TestPanel.objects.get(name=requisition_panel.name)
        aliquot_type = TestAliquotType.objects.get(alpha_code=requisition_panel.aliquot_type_alpha_code)
        test_requisition = TestRequisitionFactory(
            test_visit=self.test_visit, site=self.site, panel=panel, aliquot_type=aliquot_type, is_drawn='No')
        lab_profile = site_lab_profiles.get(test_requisition._meta.object_name)
        self.assertFalse(lab_profile().receive(test_requisition))

    def test_receives3(self):
        """Asserts that receiving the requisition more than once does not
        create additional receive and primary aliquot instances."""
        self.test_visit = self.test_visit_factory(appointment=self.appointment)
        requisition_panel = RequisitionMetaData.objects.filter(
            registered_subject=self.registered_subject)[0].lab_entry.requisition_panel
        panel = TestPanel.objects.get(name=requisition_panel.name)
        aliquot_type = TestAliquotType.objects.get(alpha_code=requisition_panel.aliquot_type_alpha_code)
        test_requisition = TestRequisitionFactory(
            test_visit=self.test_visit, site=self.site, panel=panel, aliquot_type=aliquot_type, is_drawn='Yes')
        lab_profile = site_lab_profiles.get(test_requisition._meta.object_name)
        lab_profile().receive(test_requisition)
        receive1 = TestReceive.objects.get(requisition_identifier=test_requisition.requisition_identifier)
        TestAliquot.objects.get(receive=receive1)
        # receive again, harmlessly
        lab_profile().receive(test_requisition)
        receive2 = TestReceive.objects.get(requisition_identifier=test_requisition.requisition_identifier)
        TestAliquot.objects.get(receive=receive2)
        self.assertEqual(receive1.receive_identifier, receive2.receive_identifier)
