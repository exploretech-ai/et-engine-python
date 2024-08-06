import pytest
from et_engine import vfs

# # NOTE: Create is skipped in this test

# def test_list():
#     list_of_vfs = vfs.list_all()

# def test_connect():
#     hbm = vfs.connect("hot-breccia-mapper")
#     assert isinstance(hbm, vfs.VirtualFileSystem)
    
#     with pytest.raises(NameError) as e_info:
#         vfs.connect("not-a-vfs")

# # NOTE: Delete is skipped in this test


# def test_list_dir():
#     hbm = vfs.connect("hot-breccia-mapper")
#     hbm.list()


def test_upload():

    # Regular upload
    vfs.multipart_upload("/Users/ammilten/Documents/ExploreTech/Customers/Lithium Americas/data/Satellite Imagery/S2A_MSIL2A_20230801T071211_N0509_R020_T38KQC_20230801T100950.zip", "geotiff.zip")


    # Multipart upload


# def test_download():
#     vfs.multipart_download("README.md", "README2.md")

