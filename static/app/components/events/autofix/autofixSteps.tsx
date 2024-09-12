import {Fragment} from 'react';
import styled from '@emotion/styled';
import {AnimatePresence, type AnimationProps, motion} from 'framer-motion';

import {AutofixChanges} from 'sentry/components/events/autofix/autofixChanges';
import AutofixInsightCards from 'sentry/components/events/autofix/autofixInsightCards';
import AutofixMessageBox from 'sentry/components/events/autofix/autofixMessageBox';
import {AutofixRootCause} from 'sentry/components/events/autofix/autofixRootCause';
import {
  type AutofixData,
  type AutofixProgressItem,
  type AutofixRepository,
  type AutofixStep,
  AutofixStepType,
} from 'sentry/components/events/autofix/types';
import {space} from 'sentry/styles/space';
import testableTransition from 'sentry/utils/testableTransition';

const animationProps: AnimationProps = {
  exit: {opacity: 0},
  initial: {opacity: 0},
  animate: {opacity: 1},
  transition: testableTransition({duration: 0.3}),
};
interface StepProps {
  groupId: string;
  onRetry: () => void;
  repos: AutofixRepository[];
  runId: string;
  step: AutofixStep;
  totalSteps: number;
  stepNumber?: number;
}

interface AutofixStepsProps {
  data: AutofixData;
  groupId: string;
  onRetry: () => void;
  runId: string;
}

function isProgressLog(
  item: AutofixProgressItem | AutofixStep
): item is AutofixProgressItem {
  return 'message' in item && 'timestamp' in item;
}

function replaceHeadersWithBold(markdown: string) {
  const headerRegex = /^(#{1,6})\s+(.*)$/gm;
  const boldMarkdown = markdown.replace(headerRegex, (_match, _hashes, content) => {
    return ` **${content}** `;
  });

  return boldMarkdown;
}

export function Step({
  step,
  groupId,
  runId,
  onRetry,
  repos,
  stepNumber,
  totalSteps,
}: StepProps) {
  const isActive = step.status !== 'PENDING' && step.status !== 'CANCELLED';

  return (
    <StepCard active={isActive}>
      <ContentWrapper>
        <AnimatePresence initial={false}>
          <AnimationWrapper key="content" {...animationProps}>
            <Fragment>
              {step.completedMessage && <StepBody>{step.completedMessage}</StepBody>}
              {step.type === AutofixStepType.DEFAULT && (
                <AutofixInsightCards
                  insights={step.insights}
                  repos={repos}
                  hasStepBelow={
                    stepNumber !== undefined ? stepNumber < totalSteps : false
                  }
                  hasStepAbove={stepNumber !== undefined ? stepNumber > 1 : false}
                />
              )}
              {step.type === AutofixStepType.ROOT_CAUSE_ANALYSIS && (
                <AutofixRootCause
                  groupId={groupId}
                  runId={runId}
                  causes={step.causes}
                  rootCauseSelection={step.selection}
                  repos={repos}
                />
              )}
              {step.type === AutofixStepType.CHANGES && (
                <AutofixChanges step={step} groupId={groupId} onRetry={onRetry} />
              )}
            </Fragment>
          </AnimationWrapper>
        </AnimatePresence>
      </ContentWrapper>
    </StepCard>
  );
}

export function AutofixSteps({data, groupId, runId, onRetry}: AutofixStepsProps) {
  const steps = data.steps;
  const repos = data.repositories;

  if (!steps) {
    return null;
  }

  const lastStep = steps[steps.length - 1];
  const logs: AutofixProgressItem[] = lastStep.progress?.filter(isProgressLog) ?? [];
  const activeLog =
    lastStep.completedMessage ?? replaceHeadersWithBold(logs.at(-1)?.message ?? '') ?? '';

  return (
    <div>
      <StepsContainer>
        {steps.map((step, index) => (
          <Step
            step={step}
            key={step.id}
            stepNumber={index + 1}
            totalSteps={steps.length}
            groupId={groupId}
            runId={runId}
            onRetry={onRetry}
            repos={repos}
          />
        ))}
      </StepsContainer>

      <AutofixMessageBox
        displayText={activeLog ?? ''}
        step={lastStep}
        inputPlaceholder={'Say something...'}
        responseRequired={false}
        onSend={null}
        actionText={'Send'}
        allowEmptyMessage={false}
      />
    </div>
  );
}

const StepsContainer = styled('div')`
  margin-bottom: 15em;
`;

const StepCard = styled('div')<{active?: boolean}>`
  opacity: ${p => (p.active ? 1 : 0.6)};
  overflow: hidden;

  :last-child {
    margin-bottom: 0;
  }
`;

const StepBody = styled('p')`
  padding: 0 ${space(2)} ${space(2)} ${space(2)};
  margin: -${space(1)} 0 0 0;
`;

const ContentWrapper = styled(motion.div)`
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 300ms;
  will-change: grid-template-rows;

  > div {
    /* So that focused element outlines don't get cut off */
    padding: 0 1px;
    overflow: hidden;
  }
`;

const AnimationWrapper = styled(motion.div)``;
