"""Student-specific deterministic parameters from the handout."""
import hashlib


def get_student_params(student_id: str):
    if not student_id.isdigit() or len(student_id) != 8:
        raise ValueError('Use your exact 8-digit Student ID')
    h = int(hashlib.sha256(student_id.encode('utf-8')).hexdigest()[:8], 16)
    return {'student_id': student_id, 'N': 1024 + ((h % 9) * 64),
            'buffer_elements': 16_777_216, 'seed': h % 100_007}
