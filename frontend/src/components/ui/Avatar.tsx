/**
 * 頭像組件 - VS Code 風格的用戶頭像和圖標展示組件
 * 支持圖片、文字、圖標等多種展示方式
 */

import React from 'react';
import styled from 'styled-components';
import { getThemeColors, spacing, borderRadius, transitions, shadows } from '../../styles/GlobalStyles';

// 頭像容器
const AvatarContainer = styled.div<{
  theme: 'light' | 'dark';
  size: 'small' | 'medium' | 'large' | 'extra-large';
  shape: 'circle' | 'square';
  bordered?: boolean;
  clickable?: boolean;
}>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background-color: ${props => getThemeColors(props.theme).background.tertiary};
  color: ${props => getThemeColors(props.theme).text.primary};
  font-weight: 500;
  transition: ${transitions.fast};
  
  ${props => {
    const sizeMap = {
      'small': '24px',
      'medium': '32px',
      'large': '40px',
      'extra-large': '64px'
    };
    const size = sizeMap[props.size];
    return `
      width: ${size};
      height: ${size};
      font-size: ${props.size === 'small' ? '12px' : props.size === 'medium' ? '14px' : props.size === 'large' ? '16px' : '24px'};
    `;
  }}
  
  border-radius: ${props => props.shape === 'circle' ? '50%' : borderRadius.sm};
  
  ${props => props.bordered && `
    border: 2px solid ${getThemeColors(props.theme).border.primary};
  `}
  
  ${props => props.clickable && `
    cursor: pointer;
    
    &:hover {
      background-color: ${getThemeColors(props.theme).background.hover};
      transform: scale(1.05);
    }
  `}
`;

// 頭像圖片
const AvatarImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
`;

// 頭像文字
const AvatarText = styled.span<{
  theme: 'light' | 'dark';
}>`
  color: ${props => getThemeColors(props.theme).text.primary};
  font-weight: 600;
  text-transform: uppercase;
  user-select: none;
`;

// 頭像圖標
const AvatarIcon = styled.div<{
  theme: 'light' | 'dark';
}>`
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => getThemeColors(props.theme).text.secondary};
`;

// 頭像徽章
const AvatarBadge = styled.div<{
  theme: 'light' | 'dark';
  status: 'online' | 'offline' | 'away' | 'busy';
  size: 'small' | 'medium' | 'large' | 'extra-large';
}>`
  position: absolute;
  bottom: 0;
  right: 0;
  border-radius: 50%;
  border: 2px solid ${props => getThemeColors(props.theme).background.primary};
  
  ${props => {
    const sizeMap = {
      'small': '8px',
      'medium': '10px',
      'large': '12px',
      'extra-large': '16px'
    };
    const size = sizeMap[props.size];
    return `
      width: ${size};
      height: ${size};
    `;
  }}
  
  background-color: ${props => {
    const colors = getThemeColors(props.theme);
    switch (props.status) {
      case 'online': return colors.status.success;
      case 'offline': return colors.text.disabled;
      case 'away': return colors.status.warning;
      case 'busy': return colors.status.error;
      default: return colors.text.disabled;
    }
  }};
`;

// 頭像組合容器
const AvatarGroup = styled.div<{
  theme: 'light' | 'dark';
  maxCount?: number;
}>`
  display: flex;
  align-items: center;
  
  ${AvatarContainer} {
    margin-left: -8px;
    border: 2px solid ${props => getThemeColors(props.theme).background.primary};
    
    &:first-child {
      margin-left: 0;
    }
    
    &:hover {
      z-index: 1;
    }
  }
`;

// 更多頭像指示器
const MoreAvatars = styled(AvatarContainer)`
  background-color: ${props => getThemeColors(props.theme).background.tertiary};
  color: ${props => getThemeColors(props.theme).text.secondary};
  font-size: 12px;
  font-weight: 500;
`;

// 頭像組件介面
export interface AvatarProps {
  theme: 'light' | 'dark';
  size?: 'small' | 'medium' | 'large' | 'extra-large';
  shape?: 'circle' | 'square';
  src?: string;
  alt?: string;
  text?: string;
  icon?: React.ReactNode;
  bordered?: boolean;
  status?: 'online' | 'offline' | 'away' | 'busy';
  onClick?: (e: React.MouseEvent) => void;
  className?: string;
}

/**
 * 頭像組件
 * 用於顯示用戶頭像、圖標或文字標識
 */
export const Avatar: React.FC<AvatarProps> = ({
  theme,
  size = 'medium',
  shape = 'circle',
  src,
  alt,
  text,
  icon,
  bordered = false,
  status,
  onClick,
  className
}) => {
  // 生成文字頭像的初始字母
  const getInitials = (text: string): string => {
    if (!text) return '';
    const words = text.trim().split(' ');
    if (words.length === 1) {
      return words[0].charAt(0);
    }
    return words[0].charAt(0) + words[1].charAt(0);
  };
  
  const renderContent = () => {
    if (src) {
      return (
        <AvatarImage
          src={src}
          alt={alt || 'Avatar'}
          onError={(e) => {
            // 圖片載入失敗時隱藏圖片，顯示文字或圖標
            e.currentTarget.style.display = 'none';
          }}
        />
      );
    }
    
    if (text) {
      return (
        <AvatarText theme={theme}>
          {getInitials(text)}
        </AvatarText>
      );
    }
    
    if (icon) {
      return (
        <AvatarIcon theme={theme}>
          {icon}
        </AvatarIcon>
      );
    }
    
    // 預設用戶圖標
    return (
      <AvatarIcon theme={theme}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
        </svg>
      </AvatarIcon>
    );
  };
  
  return (
    <AvatarContainer
      theme={theme}
      size={size}
      shape={shape}
      bordered={bordered}
      clickable={!!onClick}
      onClick={onClick}
      className={className}
    >
      {renderContent()}
      
      {status && (
        <AvatarBadge
          theme={theme}
          status={status}
          size={size}
        />
      )}
    </AvatarContainer>
  );
};

// 頭像組合組件介面
export interface AvatarGroupProps {
  theme: 'light' | 'dark';
  size?: 'small' | 'medium' | 'large' | 'extra-large';
  shape?: 'circle' | 'square';
  maxCount?: number;
  children: React.ReactElement<AvatarProps>[];
  className?: string;
}

/**
 * 頭像組合組件
 * 用於顯示多個頭像的組合
 */
export const AvatarGroup: React.FC<AvatarGroupProps> = ({
  theme,
  size = 'medium',
  shape = 'circle',
  maxCount = 5,
  children,
  className
}) => {
  const avatars = React.Children.toArray(children) as React.ReactElement<AvatarProps>[];
  const visibleAvatars = avatars.slice(0, maxCount);
  const remainingCount = avatars.length - maxCount;
  
  return (
    <AvatarGroup theme={theme} maxCount={maxCount} className={className}>
      {visibleAvatars.map((avatar, index) => 
        React.cloneElement(avatar, {
          key: index,
          theme,
          size,
          shape,
          bordered: true
        })
      )}
      
      {remainingCount > 0 && (
        <MoreAvatars
          theme={theme}
          size={size}
          shape={shape}
          bordered={true}
          clickable={false}
        >
          +{remainingCount}
        </MoreAvatars>
      )}
    </AvatarGroup>
  );
};

// 用戶頭像組件介面
export interface UserAvatarProps {
  theme: 'light' | 'dark';
  user: {
    id: string;
    name: string;
    avatar?: string;
    email?: string;
    status?: 'online' | 'offline' | 'away' | 'busy';
  };
  size?: 'small' | 'medium' | 'large' | 'extra-large';
  shape?: 'circle' | 'square';
  showName?: boolean;
  showStatus?: boolean;
  onClick?: (user: any) => void;
  className?: string;
}

/**
 * 用戶頭像組件
 * 專門用於顯示用戶資訊的頭像組件
 */
export const UserAvatar: React.FC<UserAvatarProps> = ({
  theme,
  user,
  size = 'medium',
  shape = 'circle',
  showName = false,
  showStatus = true,
  onClick,
  className
}) => {
  const UserContainer = styled.div`
    display: flex;
    align-items: center;
    gap: ${spacing.sm};
    cursor: ${onClick ? 'pointer' : 'default'};
    
    &:hover {
      opacity: ${onClick ? '0.8' : '1'};
    }
  `;
  
  const UserInfo = styled.div`
    display: flex;
    flex-direction: column;
    gap: 2px;
  `;
  
  const UserName = styled.span`
    color: ${getThemeColors(theme).text.primary};
    font-size: 14px;
    font-weight: 500;
    line-height: 1.2;
  `;
  
  const UserEmail = styled.span`
    color: ${getThemeColors(theme).text.secondary};
    font-size: 12px;
    line-height: 1.2;
  `;
  
  const handleClick = () => {
    if (onClick) {
      onClick(user);
    }
  };
  
  return (
    <UserContainer onClick={handleClick} className={className}>
      <Avatar
        theme={theme}
        size={size}
        shape={shape}
        src={user.avatar}
        text={user.name}
        status={showStatus ? user.status : undefined}
        bordered
      />
      
      {showName && (
        <UserInfo>
          <UserName>{user.name}</UserName>
          {user.email && (
            <UserEmail>{user.email}</UserEmail>
          )}
        </UserInfo>
      )}
    </UserContainer>
  );
};

export default Avatar;