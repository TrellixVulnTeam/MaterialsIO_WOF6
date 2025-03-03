from materials_io.dft import DFTParser
from shutil import copy
from glob import glob
import tarfile
import pytest
import os

vasp_tar = os.path.join(os.path.dirname(__file__), 'data',
                        'vasp', 'AlNi_static_LDA.tar.gz')
pwscf_tar = os.path.join(os.path.dirname(__file__), 'data',
                         'pwscf', 'NaF.scf.tar.gz')


@pytest.fixture
def vasp_dir(tmpdir):
    """Unpack VASP tar into a temporary directory"""
    with tarfile.open(vasp_tar) as fp:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(fp, tmpdir)
    return str(tmpdir)


@pytest.fixture
def parser():
    return DFTParser(quality_report=False)


@pytest.fixture
def multi_vasp_dir(vasp_dir):
    """VASP directory with two calculations with different extensions"""
    for f in glob(os.path.join(os.path.join(vasp_dir, 'AlNi_static_LDA'), '*')):
        if os.path.isfile(f):
            copy(f, f + '.2')
    return str(vasp_dir)


@pytest.fixture
def pwscf_dir(tmpdir):
    with tarfile.open(pwscf_tar) as fp:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(fp, tmpdir)
    return str(tmpdir)


def test_single_vasp_calc(parser, vasp_dir):
    metadata = list(parser.parse_directory(vasp_dir))
    assert len(metadata) == 1
    assert isinstance(metadata[0], tuple)
    assert isinstance(metadata[0][0], list)
    assert isinstance(metadata[0][1], dict)


def test_multivasp_calc(parser: DFTParser, multi_vasp_dir):
    metadata = list(parser.parse_directory(multi_vasp_dir))
    assert len(metadata) == 2
    assert isinstance(metadata[0][0], list)
    assert isinstance(metadata[0][1], dict)


def test_pwscf(parser: DFTParser, pwscf_dir):
    metadata = list(parser.parse_directory(pwscf_dir))
    assert len(metadata) == 1
