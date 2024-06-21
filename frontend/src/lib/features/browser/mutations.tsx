import { useMutation } from '@tanstack/react-query';
import { authAxios } from '$auth/state/auth';

export const useDeleteInterface = () => {
  return useMutation({
    mutationFn: async (interfaceId: string) => {
      const response = await authAxios.delete(`/v1/metadata/interfaces/${interfaceId}/`);
      return response.data;
    },
    onError: (error) => {
      console.error('Error deleting interface:', error);
    },
  });
};
