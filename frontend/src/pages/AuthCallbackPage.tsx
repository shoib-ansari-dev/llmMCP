import { useNavigate } from 'react-router-dom';
import { AuthCallbackPage as AuthCallbackComponent } from '../auth';

export function AuthCallbackPage() {
  const navigate = useNavigate();

  return (
    <AuthCallbackComponent
      onSuccess={() => {
        navigate('/dashboard');
      }}
      onError={() => {
        navigate('/login');
      }}
    />
  );
}

