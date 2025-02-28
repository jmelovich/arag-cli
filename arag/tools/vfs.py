import apsw
import zipfile

class ZipVFS(apsw.VFS):
    """Custom VFS to access files inside a zip archive."""
    def __init__(self, name):
        # Initialize with the default VFS as the base
        apsw.VFS.__init__(self, name, base="", makedefault=False)

    def xOpen(self, name, flags):
        """
        Open a file. If the name is a URI with an 'archive' parameter,
        access the file from the specified zip archive.
        """
        if isinstance(name, apsw.URIFilename):
            archive = name.uri_parameter("archive")
            if archive:
                # Open the zip archive
                zipf = zipfile.ZipFile(archive, 'r')
                try:
                    info = zipf.getinfo('corpus.db')
                except KeyError:
                    raise IOError("corpus.db not found in archive")
                # Ensure the file is uncompressed
                if info.compress_type != zipfile.ZIP_STORED:
                    raise IOError("corpus.db is compressed")
                # Get a file object for random access
                fileobj = zipf.open('corpus.db')
                # Set output flags to read-only
                flags[1] = apsw.SQLITE_OPEN_READONLY
                return ZipVFSFile(fileobj, info.file_size)
        # Fallback to default VFS behavior for regular files
        return super().xOpen(name, flags)

class ZipVFSFile(apsw.VFSFile):
    """Custom VFSFile to provide read-only access to a file in the archive."""
    def __init__(self, fileobj, filesize):
        self.fileobj = fileobj  # ZipExtFile object
        self.filesize = filesize

    def xClose(self):
        """Close the file object."""
        self.fileobj.close()

    def xRead(self, amount, offset):
        """Read 'amount' bytes starting at 'offset'."""
        self.fileobj.seek(offset)
        data = self.fileobj.read(amount)
        if len(data) < amount:
            raise apsw.IOError("Short read from file")
        return data

    def xFileSize(self):
        """Return the size of the file."""
        return self.filesize

    def xLock(self, level):
        """Support only shared locks for read-only access."""
        if level > apsw.SQLITE_LOCK_SHARED:
            raise apsw.BusyError("Cannot lock for writing")
        # Shared lock is a no-op

    def xUnlock(self, level):
        """Unlocking is a no-op."""
        pass

    def xCheckReservedLock(self):
        """No reserved locks in read-only mode."""
        return False

    def xFileControl(self, op, ptr):
        """Handle file control operations; return False for unrecognized ops."""
        return False

    def xSectorSize(self):
        """Return a default sector size."""
        return 4096

    def xDeviceCharacteristics(self):
        """Return default device characteristics."""
        return 0

# Register the custom VFS globally
zip_vfs = ZipVFS("zipvfs")