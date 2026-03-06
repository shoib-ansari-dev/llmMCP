import { useSearchParams, useNavigate } from 'react-router-dom';
import { ResetPage as ResetPageComponent } from '../auth';

export function ResetPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  return (
    <ResetPageComponent
      token={token}
      onSuccess={() => {
        navigate('/login');
      }}
    />
  );
}

