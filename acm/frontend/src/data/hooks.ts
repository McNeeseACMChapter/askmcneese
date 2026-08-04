import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";
import { fixtureRepo } from "./repository";
import { qk } from "./queryKeys";
import { computePulse } from "./seed";
import { acmApi, type ProjectUpdateInput } from "./apiClient";

export function useFixtureState() {
  return useSyncExternalStore(
    fixtureRepo.subscribe,
    fixtureRepo.getSnapshot,
    fixtureRepo.getSnapshot,
  );
}

export function usePulseQuery() {
  const state = useFixtureState();
  return {
    data: computePulse(state),
    isLoading: false,
  };
}


export function useAccessContractQuery() {
  return useQuery({
    queryKey: ["acm", "access-contract"],
    queryFn: acmApi.getAccessContract,
    retry: false,
    staleTime: 60_000,
  });
}

export function useUpdateProjectMutation() {
  return useMutation({
    mutationFn: (input: ProjectUpdateInput) => fixtureRepo.updateProject(input),
  });
}
export function useProjectsQuery() {
  const state = useFixtureState();
  return {
    data: state.projects.filter((p) => !p.archived),
    isLoading: false,
  };
}

export function useProjectQuery(id: string) {
  const state = useFixtureState();
  return {
    data: state.projects.find((p) => p.id === id),
    isLoading: false,
  };
}

export function useApprovalQuery(id: string) {
  const state = useFixtureState();
  return {
    data: state.approvals.find((a) => a.id === id),
    isLoading: false,
  };
}

export function useAsyncProjectsQuery() {
  return useQuery({
    queryKey: qk.projects,
    queryFn: () => fixtureRepo.getProjects(),
  });
}

export function useDecideApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fixtureRepo.decideApproval,
    onSuccess: async () => {
      await qc.invalidateQueries();
    },
  });
}

export function useAttachEvidenceMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      approvalId,
      evidenceId,
      roleId,
    }: {
      approvalId: string;
      evidenceId: string;
      roleId: import("./types").RoleId;
    }) => fixtureRepo.attachEvidence(approvalId, evidenceId, roleId),
    onSuccess: async () => {
      await qc.invalidateQueries();
    },
  });
}
