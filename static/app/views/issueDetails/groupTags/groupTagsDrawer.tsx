import {useRef, useState} from 'react';
import styled from '@emotion/styled';

import ProjectAvatar from 'sentry/components/avatar/projectAvatar';
import {Button} from 'sentry/components/button';
import {ExportQueryType, useDataExport} from 'sentry/components/dataExport';
import {DropdownMenu} from 'sentry/components/dropdownMenu';
import {
  CrumbContainer,
  EventDrawerBody,
  EventDrawerContainer,
  EventDrawerHeader,
  EventNavigator,
  Header,
  NavigationCrumbs,
  ShortId,
} from 'sentry/components/events/eventDrawer';
import LoadingError from 'sentry/components/loadingError';
import LoadingIndicator from 'sentry/components/loadingIndicator';
import {IconDownload} from 'sentry/icons';
import {t} from 'sentry/locale';
import {space} from 'sentry/styles/space';
import type {Group} from 'sentry/types/group';
import {useLocation} from 'sentry/utils/useLocation';
import useOrganization from 'sentry/utils/useOrganization';
import {useParams} from 'sentry/utils/useParams';
import useProjects from 'sentry/utils/useProjects';
import {TagDetailsDrawerContent} from 'sentry/views/issueDetails/groupTags/tagDetailsDrawerContent';
import {TagDistribution} from 'sentry/views/issueDetails/groupTags/tagDistribution';
import {useGroupTags} from 'sentry/views/issueDetails/groupTags/useGroupTags';
import {Tab, TabPaths} from 'sentry/views/issueDetails/types';
import {useGroupDetailsRoute} from 'sentry/views/issueDetails/useGroupDetailsRoute';

export function GroupTagsDrawer({group}: {group: Group}) {
  const location = useLocation();
  const organization = useOrganization();
  const {tagKey} = useParams<{tagKey: string}>();
  const drawerRef = useRef<HTMLDivElement>(null);
  const {projects} = useProjects();
  const project = projects.find(p => p.slug === group.project.slug)!;
  const [isExportDisabled, setIsExportDisabled] = useState(false);
  const {baseUrl} = useGroupDetailsRoute();
  const handleDataExport = useDataExport({
    payload: {
      queryType: ExportQueryType.ISSUES_BY_TAG,
      queryInfo: {
        project: project.id,
        group: group.id,
        key: tagKey,
      },
    },
  });

  const {
    data = [],
    isPending,
    isError,
    refetch,
  } = useGroupTags({
    groupId: group.id,
    environment: location.query.environment as string[] | string | undefined,
  });

  if (isPending) {
    return <LoadingIndicator />;
  }

  if (isError) {
    return (
      <LoadingError
        message={t('There was an error loading issue tags.')}
        onRetry={refetch}
      />
    );
  }

  const alphabeticalTags = data.sort((a, b) => a.key.localeCompare(b.key));

  return (
    <EventDrawerContainer ref={drawerRef}>
      <EventDrawerHeader>
        <NavigationCrumbs
          crumbs={[
            {
              label: (
                <CrumbContainer>
                  <ProjectAvatar project={project} />
                  <ShortId>{group.shortId}</ShortId>
                </CrumbContainer>
              ),
            },
            {
              label: t('All Tags'),
              to: tagKey
                ? {
                    pathname: `${baseUrl}${TabPaths[Tab.TAGS]}`,
                    query: location.query,
                  }
                : undefined,
            },
            ...(tagKey ? [{label: tagKey}] : []),
          ]}
        />
      </EventDrawerHeader>
      <EventNavigator>
        <Header>{tagKey ? t('Tag Details') : t('Tags')}</Header>
        {tagKey && (
          <DropdownMenu
            size="xs"
            trigger={triggerProps => (
              <Button
                {...triggerProps}
                borderless
                size="xs"
                aria-label={t('Export options')}
                icon={<IconDownload />}
              />
            )}
            items={[
              {
                key: 'export-page',
                label: t('Export Page to CSV'),
                to: `${organization.slug}/${project.slug}/issues/${group.id}/tags/${tagKey}/export/`,
              },
              {
                key: 'export-all',
                label: isExportDisabled
                  ? t('Export in progress...')
                  : t('Export All to CSV'),
                onAction: () => {
                  handleDataExport();
                  setIsExportDisabled(true);
                },
                disabled: isExportDisabled,
              },
            ]}
          />
        )}
      </EventNavigator>
      <EventDrawerBody>
        {tagKey ? (
          <TagDetailsDrawerContent
            project={project}
            groupId={group.id}
            drawerRef={drawerRef}
          />
        ) : (
          <Wrapper>
            <Container>
              {alphabeticalTags.map((tag, tagIdx) => (
                <TagDistribution tag={tag} key={tagIdx} />
              ))}
            </Container>
          </Wrapper>
        )}
      </EventDrawerBody>
    </EventDrawerContainer>
  );
}

const Wrapper = styled('div')`
  display: flex;
  flex-direction: column;
  gap: ${space(2)};
`;

const Container = styled('div')`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: ${space(2)};
  margin-bottom: ${space(2)};
`;
