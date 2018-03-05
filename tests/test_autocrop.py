# -*- coding: utf-8 -*-

"""Tests for autocrop"""

import io
import os
import shutil
import sys

try:
    import mock
except ImportError:
    from unittest import mock
import pytest
import cv2
import numpy as np

from autocrop.autocrop import (
        gamma,
        crop,
        cli,
        crop_folder,
        size,
        confirmation,
)

PY3 = (sys.version_info[0] >= 3)


@pytest.fixture()
def integration():
    # Setup
    path_i = 'tests/test'
    path_o = 'tests/crop'
    shutil.copytree('tests/data', path_i)
    yield

    # Teardown
    shutil.rmtree(path_i)
    try:
        shutil.rmtree(path_o)
    except OSError:
        pass


def test_gamma_brightens_image():
    """This function is so tightly coupled to cv2 it's probably useless.
    Still might flag cv2 or numpy boo-boos."""
    matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expected = np.uint8([[15, 22, 27], [31, 35, 39], [42, 45, 47]])
    np.testing.assert_array_equal(gamma(img=matrix, correction=0.5), expected)


def test_crop_noise_returns_none():
    loc = 'tests/data/noise.png'
    noise = cv2.imread(loc)
    assert crop(noise) is None


def test_obama_has_a_face():
    loc = 'tests/data/obama.jpg'
    obama = cv2.imread(loc)
    assert len(crop(obama, 500, 500)) == 500


def test_size_140_is_valid():
    assert size(140) == 140


def test_size_0_not_valid():
    with pytest.raises(Exception) as e:
        size(0)
    assert 'Invalid pixel' in str(e)


def test_size_million_not_valid():
    with pytest.raises(Exception) as e:
        size(1e6)
    assert 'Invalid pixel' in str(e)


def test_size_asdf_gives_ValueError():
    with pytest.raises(Exception) as e:
        size('asdf')
    assert 'ValueError' in str(e)


def test_size_minus_14_not_valid():
    with pytest.raises(Exception) as e:
        size(-14)
    assert 'Invalid pixel' in str(e)


@mock.patch('autocrop.autocrop.input_path', lambda p: p)
@mock.patch('autocrop.autocrop.crop_folder')
def test_cli_no_args_means_cwd(mock_crop_folder):
    mock_crop_folder.return_value = None
    sys.argv = ['', '--no-confirm']
    cli()
    args, _ = mock_crop_folder.call_args
    assert args == (None, None, 500, 500)


@mock.patch('autocrop.autocrop.input_path', lambda p: p)
@mock.patch('autocrop.autocrop.crop_folder')
def test_cli_width_140_is_valid(mock_crop_folder):
    mock_crop_folder.return_value = None
    sys.argv = ['autocrop', '-w', '140', '--no-confirm']
    assert mock_crop_folder.call_count == 0
    cli()
    assert mock_crop_folder.call_count == 1


def test_cli_invalid_input_path_errors_out():
    sys.argv = ['autocrop', '-i', 'asdfasdf']
    with pytest.raises(SystemExit) as e:
        cli()
    assert e.type == SystemExit
    assert 'SystemExit' in str(e)


def test_cli_no_images_in_input_path():
    sys.argv = ['autocrop', '-i', 'tests']
    with pytest.raises(SystemExit) as e:
        cli()
    assert e.type == SystemExit
    assert 'SystemExit' in str(e)


def test_cli_width_0_not_valid():
    sys.argv = ['autocrop', '-w', '0']
    with pytest.raises(SystemExit) as e:
        cli()
    assert e.type == SystemExit
    assert 'SystemExit' in str(e)


def test_cli_width_minus_14_not_valid():
    sys.argv = ['autocrop', '-w', '-14']
    with pytest.raises(SystemExit) as e:
        cli()
    assert e.type == SystemExit
    assert 'SystemExit' in str(e)


@pytest.mark.parametrize("from_user, response, output", [
    (['x', 'x', 'No'], False, "Please respond with 'y' or 'n'\n" * 2),
    (['y'], True, ''),
    (['n'], False, ''),
    (['x', 'y'], True, "Please respond with 'y' or 'n'\n"),
])
def test_confirmation_get_from_user(from_user, response, output):
    question = "Overwrite image files?"
    input_str = 'autocrop.autocrop.compat_input'

    with mock.patch(input_str, lambda x: from_user.pop(0)):
        sio = io.StringIO if PY3 else io.BytesIO
        with mock.patch('sys.stdout', new_callable=sio):
            assert response == confirmation(question)
            assert output == sys.stdout.getvalue()


@mock.patch('autocrop.autocrop.crop_folder', lambda *args: None)
@mock.patch('autocrop.autocrop.confirmation')
def test_user_gets_prompted_if_no_output_is_given(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ['', '-i', 'tests/data']
    with pytest.raises(SystemExit) as e:
        assert mock_confirm.call_count == 0
        cli()
    assert mock_confirm.call_count == 1
    assert e.type == SystemExit


@mock.patch('autocrop.autocrop.crop_folder', lambda *args: None)
@mock.patch('autocrop.autocrop.confirmation')
def test_user_gets_prompted_if_output_same_as_input(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ['', '-i', 'tests/data']
    with pytest.raises(SystemExit) as e:
        assert mock_confirm.call_count == 0
        cli()
    assert mock_confirm.call_count == 1
    assert e.type == SystemExit


def test_crop_folder_overwrites_when_same_input_and_output(integration):
    sys.argv = ['', '--no-confirm', '-i', 'tests/test', '-o', 'tests/test']
    cli()
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == 10


@mock.patch('autocrop.autocrop.crop')
def test_crop_folder_overwrites_when_no_output(mock_crop, integration):
    mock_crop.return_value = None
    assert mock_crop.call_count == 0
    crop_folder('tests/test', None)
    assert mock_crop.call_count == 9


@mock.patch('autocrop.autocrop.crop_folder', lambda *args: None)
@mock.patch('autocrop.autocrop.output_path', lambda p: p)
@mock.patch('autocrop.autocrop.confirmation')
def test_user_does_not_get_prompted_if_output_d_is_given(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ['', '-i', 'tests/data', '-o', 'tests/crop']
    assert mock_confirm.call_count == 0
    cli()
    assert mock_confirm.call_count == 0


@mock.patch('autocrop.autocrop.crop_folder', lambda *args: None)
@mock.patch('autocrop.autocrop.confirmation')
def test_user_does_not_get_prompted_if_no_confirm(mock_confirm):
    mock_confirm.return_value = False
    sys.argv = ['', '-i', 'tests/data', '--no-confirm']
    assert mock_confirm.call_count == 0
    cli()
    assert mock_confirm.call_count == 0


@mock.patch('autocrop.autocrop.crop', lambda *args: None)
def test_images_files_copied_over_if_output_dir_specified(integration):
    sys.argv = ['', '-i', 'tests/test', '-o', 'tests/crop']
    cli()
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == 9


@mock.patch('autocrop.autocrop.confirmation', lambda *args: True)
def test_image_files_overwritten_if_no_output_dir(integration):
    sys.argv = ['', '-i', 'tests/test']
    cli()
    # We have the same number of files
    output_files = os.listdir(sys.argv[-1])
    assert len(output_files) == 10
    # Images with a face have been cropped
    shape = cv2.imread('tests/test/king.jpg').shape
    assert shape == (500, 500, 3)


@mock.patch('autocrop.autocrop.confirmation', lambda *args: True)
@mock.patch('autocrop.autocrop.crop_file')
def test_calling_autocrop_with_filename_crops_it(mock_crop_file, integration):
    mock_crop_file.return_value = None
    sys.argv = ['', 'tests/test/king.jpg']
    assert mock_crop_file.call_count == 0
    cli()
    # We've made a call to crop_file
    assert mock_crop_file.call_count == 1


@mock.patch('autocrop.autocrop.confirmation', lambda *args: True)
@mock.patch('autocrop.autocrop.crop_file')
def test_cli_input_and_filename_raises_error(mock_crop_file, integration):
    mock_crop_file.return_value = None
    sys.argv = ['', 'tests/test/king.jpg', '-i', 'tests/data']
    with pytest.raises(SystemExit) as e:
        cli()
    assert e.type == SystemExit
    print(e.__name__)
    assert 'both' in str(e)


# def test_cli_just_input_flag_no_arg_throws_error():
#     assert True is False
#
#
# def test_autocrop_from_file_prompts_for_overwrite():
#     assert True is False
#
#
# def test_single_file_no_prompt_with_force_flag():
#     assert True is False
#
#
# def test_single_file_with_output_moves_it_there():
#     assert True is False
#
#
# def test_single_file_with_output_prompt_if_already_exists():
#     assert True is False
#
#
# def test_error_if_single_file_and_input_flags():
#     assert True is False
#
#
# def test_single_file_exits_with_0_for_success():
#     assert True is False
#
#
# def test_single_file_exits_with_1_for_noface():
#     assert True is False
#
#
# def test_cli_more_than_one_filename_crops_them_all():
#     assert True is Falseargument
