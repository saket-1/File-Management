# backend/files/tests.py
import io
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from .models import File, PhysicalFile

# Helper function to create a dummy file
def create_dummy_file(name="dummy.txt", content=b"This is dummy content.", content_type="text/plain"):
    return SimpleUploadedFile(name, content, content_type=content_type)

class FileAPITests(APITestCase):
    """ Tests for the File API endpoints. """

    def setUp(self):
        """ Set up initial data if needed. """
        self.list_create_url = reverse('file-list-create')
        self.stats_url = reverse('storage-stats')
        # No initial files created here

    def test_file_upload_success(self):
        """ Ensure we can upload a file successfully. """
        file_content = b"First file content"
        dummy_file = create_dummy_file(name="first.txt", content=file_content)
        
        response = self.client.post(self.list_create_url, {'file': dummy_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        
        # Check some response data
        self.assertEqual(response.data['original_name'], 'first.txt')
        # Cannot reliably test full URL hash part easily, just check start/end
        self.assertTrue(response.data['file_url'].startswith('http://testserver/media/physical_files/'))
        self.assertTrue(response.data['file_url'].endswith('.txt'))
        self.assertEqual(response.data['size'], len(file_content))
        
        # Check database state
        physical_file = PhysicalFile.objects.first()
        self.assertEqual(physical_file.size, len(file_content))

    def test_file_deduplication(self):
        """ Ensure uploading the same file content results in deduplication. """
        file_content = b"Same content for deduplication test."
        dummy_file1 = create_dummy_file(name="dup1.txt", content=file_content)
        dummy_file2 = create_dummy_file(name="dup2.log", content=file_content)

        # Upload first file
        response1 = self.client.post(self.list_create_url, {'file': dummy_file1}, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        first_physical_pk = PhysicalFile.objects.first().pk

        # Upload second file with same content but different name
        response2 = self.client.post(self.list_create_url, {'file': dummy_file2}, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify counts: 2 logical files, still only 1 physical file
        self.assertEqual(File.objects.count(), 2)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        
        # Verify both logical files point to the same physical file
        logical_files = File.objects.all().order_by('uploaded_at')
        self.assertEqual(logical_files[0].physical_file.pk, first_physical_pk)
        self.assertEqual(logical_files[1].physical_file.pk, first_physical_pk)
        self.assertEqual(logical_files[0].original_name, "dup1.txt")
        self.assertEqual(logical_files[1].original_name, "dup2.log")

    def test_file_list_filtering(self):
        """ Test filtering the file list by original_name and extension. """
        # Upload some files
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="report_final.pdf", content=b"PDF1")}, format='multipart')
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="report_draft.txt", content=b"TXT1")}, format='multipart')
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="summary.txt", content=b"TXT2")}, format='multipart')

        # Filter by name containing 'report'
        response_name = self.client.get(self.list_create_url, {'original_name': 'report'})
        self.assertEqual(response_name.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_name.data), 2) # report_final.pdf, report_draft.txt

        # Filter by extension 'txt'
        response_ext = self.client.get(self.list_create_url, {'extension': 'txt'})
        self.assertEqual(response_ext.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_ext.data), 2) # report_draft.txt, summary.txt
        self.assertEqual(response_ext.data[0]['original_name'], 'summary.txt') # Default order is -uploaded_at

        # Filter by extension 'pdf'
        response_pdf = self.client.get(self.list_create_url, {'extension': 'pdf'})
        self.assertEqual(response_pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_pdf.data), 1) 
        self.assertEqual(response_pdf.data[0]['original_name'], 'report_final.pdf')
        
        # Filter by non-existent name
        response_none = self.client.get(self.list_create_url, {'original_name': 'nonexistent'})
        self.assertEqual(response_none.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_none.data), 0) 

    def test_file_delete_cleanup(self):
        """ Test that deleting the last logical file removes the physical file. """
        # Upload a unique file
        res_upload = self.client.post(self.list_create_url, {'file': create_dummy_file(name="unique.dat", content=b"unique data")}, format='multipart')
        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        logical_file_id = res_upload.data['id']
        physical_file_pk = File.objects.get(id=logical_file_id).physical_file.pk

        # Delete the logical file
        delete_url = reverse('file-retrieve-destroy', kwargs={'pk': logical_file_id})
        res_delete = self.client.delete(delete_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

        # Verify both logical and physical files are gone
        self.assertEqual(File.objects.count(), 0)
        self.assertEqual(PhysicalFile.objects.count(), 0)
        # Check physical file doesn't exist by PK
        with self.assertRaises(PhysicalFile.DoesNotExist):
             PhysicalFile.objects.get(pk=physical_file_pk)

    def test_file_delete_deduplicated(self):
        """ Test that deleting one logical file doesn't remove a shared physical file. """
         # Upload same content twice
        content = b"shared data"
        res1 = self.client.post(self.list_create_url, {'file': create_dummy_file(name="shared1.dat", content=content)}, format='multipart')
        res2 = self.client.post(self.list_create_url, {'file': create_dummy_file(name="shared2.dat", content=content)}, format='multipart')
        self.assertEqual(File.objects.count(), 2)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        logical_file_id_1 = res1.data['id']
        physical_file_pk = File.objects.get(id=logical_file_id_1).physical_file.pk

        # Delete the first logical file
        delete_url = reverse('file-retrieve-destroy', kwargs={'pk': logical_file_id_1})
        res_delete = self.client.delete(delete_url)
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

        # Verify one logical file remains, physical file still exists
        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(PhysicalFile.objects.count(), 1)
        self.assertTrue(PhysicalFile.objects.filter(pk=physical_file_pk).exists()) # Check physical still there

    def test_storage_stats(self):
        """ Test the storage statistics endpoint. """
        # Initial state
        res_initial = self.client.get(self.stats_url)
        self.assertEqual(res_initial.status_code, status.HTTP_200_OK)
        self.assertEqual(res_initial.data['logical_file_count'], 0)
        self.assertEqual(res_initial.data['physical_file_count'], 0)
        self.assertEqual(res_initial.data['storage_savings_bytes'], 0)

        # Upload two unique files
        content1 = b"File content one." # 17 bytes
        content2 = b"File content two is longer." # 27 bytes
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="f1.txt", content=content1)}, format='multipart')
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="f2.txt", content=content2)}, format='multipart')
        
        res_two_unique = self.client.get(self.stats_url)
        
        self.assertEqual(res_two_unique.data['logical_file_count'], 2)
        self.assertEqual(res_two_unique.data['physical_file_count'], 2)
        # Use correct expected sum (17 + 27 = 44)
        self.assertEqual(res_two_unique.data['total_logical_size_bytes'], 17 + 27) 
        self.assertEqual(res_two_unique.data['total_physical_size_bytes'], 17 + 27)
        self.assertEqual(res_two_unique.data['storage_savings_bytes'], 0) # No savings yet

        # Upload a duplicate of the first file
        self.client.post(self.list_create_url, {'file': create_dummy_file(name="f1_dup.txt", content=content1)}, format='multipart')

        res_one_dup = self.client.get(self.stats_url)
        self.assertEqual(res_one_dup.data['logical_file_count'], 3) # 3 logical files
        self.assertEqual(res_one_dup.data['physical_file_count'], 2) # Still 2 physical files
        # Use correct expected sums (17 + 27 + 17 = 61; 17 + 27 = 44)
        self.assertEqual(res_one_dup.data['total_logical_size_bytes'], 17 + 27 + 17) 
        self.assertEqual(res_one_dup.data['total_physical_size_bytes'], 17 + 27) 
        self.assertEqual(res_one_dup.data['storage_savings_bytes'], 17) # Saved 17 bytes 