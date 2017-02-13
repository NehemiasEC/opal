"""
Unittests for the opal.core.discoverable module
"""
from mock import patch
from django.test import override_settings

from opal.core import exceptions
from opal.core.test import OpalTestCase
from opal.utils import AbstractBase

from opal.core import discoverable

"""
BEGIN COMPLICATED CLASS SETUP
"""
class NewOpalObjectType(object):
    pass

class NewOpalObjectClass(NewOpalObjectType):
    pass

class MyPassingFeature(discoverable.DiscoverableFeature):
    pass

class WatFeature(discoverable.DiscoverableFeature):
    display_name = 'wat'
    module_name = 'wat'

class SlugFeature(discoverable.DiscoverableFeature):
    module_name = 'sluggy'

class MySlugFeature(SlugFeature):
    slug = 'my-slug'
    display_name = 'My Slug Defined Slug'

class ColourFeature(discoverable.DiscoverableFeature):
    module_name = 'colours'

class BlueColour(ColourFeature):
    display_name = 'Blue'

class RedColour(ColourFeature):
    display_name = 'Red'

class SeaGreenColour(ColourFeature):
    display_name = 'Sea Green'

class BombManager(discoverable.DiscoverableManager):
    pass

class BombFeature(discoverable.DiscoverableFeature):
    module_name = 'bombs'
    blow_up = False
    implementations = BombManager()

    @classmethod
    def is_valid(klass):
        if klass.blow_up == True:
            from opal.core.exceptions import InvalidDiscoverableFeatureError
            raise InvalidDiscoverableFeatureError('BLOWING UP')


class Threat(BombFeature):
    pass

class AbstractThreat(BombFeature, AbstractBase):
    pass

class SortedFeature(discoverable.SortableFeature,
                    discoverable.DiscoverableFeature):
    module_name = 'sorted'

class Sorted2(SortedFeature):
    order = 2

class Sorted3(SortedFeature):
    order = 3

class Sorted1(SortedFeature):
    order = 1

class SometimesFeature(discoverable.DiscoverableFeature,
                       discoverable.RestrictableFeature):
    module_name = 'sometimes'

class Available(SometimesFeature): pass

class Unavailable(SometimesFeature):

    @classmethod
    def visible_to(self, user):
        return False


"""
END COMPLICATED CLASS SETUP

BEGIN TEST CASES
"""

class AppImporterTestCase(OpalTestCase):

    @override_settings(INSTALLED_APPS=("opal",))
    @patch("opal.core.discoverable.stringport")
    def test_class_import(self, stringport_mock):
        classes_1 = discoverable.get_subclass("someModule", NewOpalObjectType)
        classes_2 = discoverable.get_subclass("someModule", NewOpalObjectType)

        self.assertEqual([i for i in classes_1], [NewOpalObjectClass])
        self.assertEqual([i for i in classes_2], [NewOpalObjectClass])

        # should only be called once because we should only import once
        self.assertEqual(stringport_mock.call_count, 1)


class DiscoverableManagerTestCase(OpalTestCase):

    def test_set_up_by_default_by_metaclass(self):
        self.assertIsInstance(
            ColourFeature.implementations,
            discoverable.DiscoverableManager
        )

    def test_if_overidden_dont_kill_override_in_metaclass(self):
        self.assertNotEqual(
                BombFeature.implementations.__class__,
                discoverable.DiscoverableManager
        )
        self.assertIsInstance(
            BombFeature.implementations,
            BombManager
        )

    def test_if_overridden_by_non_manager_class_blow_up(self):
        with self.assertRaises(ValueError):
            class SillyFeature(discoverable.DiscoverableFeature):
                implementations = str()

    def test_no_manager_on_subclasses(self):
        self.assertEqual(None, BlueColour.implementations)

    def test_manager_on_abstract_base_subclasses(self):
        self.assertIsInstance(
            AbstractThreat.implementations,
            discoverable.DiscoverableManager
        )

    def test_manager_knows_about_feature(self):
        self.assertEqual(ColourFeature, ColourFeature.implementations.feature)

    def test_all(self):
        self.assertEqual(
            [BlueColour, RedColour, SeaGreenColour],
            ColourFeature.implementations.all()
        )

    # TODO: Validity
    # TODO: No module_name ????

    def test_all_empty(self):
        self.assertEqual([], WatFeature.implementations.all())

    def test_get(self):
        self.assertEqual(
            MySlugFeature,
            SlugFeature.implementations.get(slug='my-slug')
        )
        self.assertEqual(
            MySlugFeature,
            SlugFeature.implementations.get(display_name='My Slug Defined Slug')
        )

    def test_get_not_an_attr(self):
        with self.assertRaises(ValueError):
            ColourFeature.implementations.get(notarealthing='Homeopathy')

    def test_get_many_attributes(self):
        self.assertEqual(
            MySlugFeature,
            SlugFeature.implementations.get(
                slug='my-slug',
                display_name='My Slug Defined Slug'
            )
        )

    def test_get_many_attributes_some_no_match(self):
        with self.assertRaises(ValueError):
            SlugFeature.implementations.get(
                slug='not-my-slug',
                display_name='My Slug Defined Slug'
            )

    def test_get_more_than_one_raises(self):
        with self.assertRaises(ValueError):
            ColourFeature.implementations.get(module_name='colours')

    def test_get_no_results_raises(self):
        with self.assertRaises(ValueError):
            ColourFeature.implementations.get(display_name='Wednesday')

    def test_filter(self):
        self.assertEqual(
            [MySlugFeature],
            SlugFeature.implementations.filter(slug='my-slug')
        )
        self.assertEqual(
            [MySlugFeature],
            SlugFeature.implementations.filter(display_name='My Slug Defined Slug')
        )

    def test_filter_returns_many(self):
        self.assertEqual(
            [BlueColour, RedColour, SeaGreenColour],
            ColourFeature.implementations.filter(module_name='colours')
        )

    def test_filter_not_an_attr(self):
        with self.assertRaises(ValueError):
            ColourFeature.implementations.filter(notarealthing='Homeopathy')


    def test_filter_many_attributes(self):
        self.assertEqual(
            [MySlugFeature],
            SlugFeature.implementations.filter(
                slug='my-slug',
                display_name='My Slug Defined Slug'
            )
        )

    def test_filter_no_results(self):
        self.assertEqual(
            [],
            SlugFeature.implementations.filter(
                slug='lol-nobody-would-choose-this-as-a-slug',
            )
        )

    def test_filter_many_attributes_one_not_an_attr(self):
        self.assertEqual(
            [],
            SlugFeature.implementations.filter(
                slug='not-my-slug',
                display_name='My Slug Defined Slug'
            )
        )



class DiscoverableFeatureTestCase(OpalTestCase):

    def test_is_valid_will_blow_up(self):

        # We only care that the above class did not raise an exception.
        self.assertTrue(True)

        with self.assertRaises(exceptions.InvalidDiscoverableFeatureError):
            class Detonate(BombFeature):
                blow_up = True

    def test_slug_for_no_implementation(self):
        with self.assertRaises(ValueError):
            MyPassingFeature.get_slug()

    def test_slug_for_implementation(self):
        self.assertEqual('wat', WatFeature.get_slug())

    def test_slug_for_subclass(self):
        self.assertEqual('red', RedColour.get_slug())

    def test_slug_for_multi_word_name(self):
        self.assertEqual('sea_green', SeaGreenColour.get_slug())

    def test_slug_for_overriden_slug_property(self):
        self.assertEqual('my-slug', MySlugFeature.get_slug())

    def test_list_for_no_implementation(self):
        with self.assertRaises(ValueError):
            MyPassingFeature.list()

    def test_list_no_subclasses(self):
        self.assertEqual([], list(WatFeature.list()))

    def test_list_subclasses(self):
        subs = list(ColourFeature.list())
        self.assertEqual(3, len(subs))
        for s in [BlueColour, RedColour, SeaGreenColour]:
            self.assertIn(s, subs)

    def test_list_invalid_subclasses(self):
        self.assertEqual([Threat], list(BombFeature.list()))

    def test_get_not_a_thing(self):
        with self.assertRaises(ValueError):
            ColourFeature.get('border_collie')

    def test_get_exists(self):
        self.assertEqual(RedColour, ColourFeature.get('red'))


    def test_abstract_discoverable(self):
        class A(discoverable.DiscoverableFeature):
            module_name = 'a'

        class AA(A, AbstractBase):
            pass

        class B(A):
            pass

        class C(B, AbstractBase):
            pass

        class D(C):
            pass

        class E(AA):
            pass

        results = {i for i in A.list()}
        self.assertEqual(results, set([B, D, E]))


class SortableFeatureTestCase(OpalTestCase):

    def test_list_respects_order(self):
        expected = [Sorted1, Sorted2, Sorted3]
        self.assertEqual(expected, list(SortedFeature.list()))

    def test_sortable_without_module_name(self):
        class Nope(discoverable.SortableFeature): pass

        with self.assertRaises(ValueError):
            Nope.list()


class RestrictableFeatureTestCase(OpalTestCase):

    def test_restricted(self):
        expected = [Available]
        self.assertEqual(expected, list(SometimesFeature.for_user(self.user)))
